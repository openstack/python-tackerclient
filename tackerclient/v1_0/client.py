# Copyright 2012 OpenStack Foundation.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import logging
import time

import requests
import six.moves.urllib.parse as urlparse

from tackerclient import client
from tackerclient.common import constants
from tackerclient.common import exceptions
from tackerclient.common import serializer
from tackerclient.common import utils
from tackerclient.i18n import _

_logger = logging.getLogger(__name__)
DEFAULT_DESC_LENGTH = 25
DEFAULT_ERROR_REASON_LENGTH = 100


def exception_handler_v10(status_code, error_content):
    """Exception handler for API v1.0 client.

    This routine generates the appropriate Tacker exception according to
    the contents of the response body.

    :param status_code: HTTP error status code
    :param error_content: deserialized body of error response
    """
    error_dict = None
    if isinstance(error_content, dict):
        error_dict = error_content.get('TackerError')
    # Find real error type
    bad_tacker_error_flag = False
    if error_dict:
        # If Tacker key is found, it will definitely contain
        # a 'message' and 'type' keys?
        try:
            error_type = error_dict['type']
            error_message = error_dict['message']
            if error_dict['detail']:
                error_message += "\n" + error_dict['detail']
        except Exception:
            bad_tacker_error_flag = True
        if not bad_tacker_error_flag:
            # If corresponding exception is defined, use it.
            client_exc = getattr(exceptions, '%sClient' % error_type, None)
            # Otherwise look up per status-code client exception
            if not client_exc:
                client_exc = exceptions.HTTP_EXCEPTION_MAP.get(status_code)
            if client_exc:
                raise client_exc(message=error_message,
                                 status_code=status_code)
            else:
                raise exceptions.TackerClientException(
                    status_code=status_code, message=error_message)
        else:
            raise exceptions.TackerClientException(status_code=status_code,
                                                   message=error_dict)
    else:
        message = None
        if isinstance(error_content, dict):
            message = error_content.get('message')
        if message:
            raise exceptions.TackerClientException(status_code=status_code,
                                                   message=message)

    # If we end up here the exception was not a tacker error
    msg = "%s-%s" % (status_code, error_content)
    raise exceptions.TackerClientException(status_code=status_code,
                                           message=msg)


class APIParamsCall(object):
    """A Decorator to support formating and tenant overriding and filters."""

    def __init__(self, function):
        self.function = function

    def __get__(self, instance, owner):
        def with_params(*args, **kwargs):
            _format = instance.format
            if 'format' in kwargs:
                instance.format = kwargs['format']
            ret = self.function(instance, *args, **kwargs)
            instance.format = _format
            return ret
        return with_params


class ClientBase(object):
    """Client for the OpenStack Tacker v1.0 API.

    :param string username: Username for authentication. (optional)
    :param string user_id: User ID for authentication. (optional)
    :param string password: Password for authentication. (optional)
    :param string token: Token for authentication. (optional)
    :param string tenant_name: Tenant name. (optional)
    :param string tenant_id: Tenant id. (optional)
    :param string auth_strategy: 'keystone' by default, 'noauth' for no
                                 authentication against keystone. (optional)
    :param string auth_url: Keystone service endpoint for authorization.
    :param string service_type: Network service type to pull from the
                                keystone catalog (e.g. 'network') (optional)
    :param string endpoint_type: Network service endpoint type to pull from the
                                 keystone catalog (e.g. 'publicURL',
                                 'internalURL', or 'adminURL') (optional)
    :param string region_name: Name of a region to select when choosing an
                               endpoint from the service catalog.
    :param string endpoint_url: A user-supplied endpoint URL for the tacker
                            service.  Lazy-authentication is possible for API
                            service calls if endpoint is set at
                            instantiation.(optional)
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    :param bool insecure: SSL certificate validation. (optional)
    :param bool log_credentials: Allow for logging of passwords or not.
                                 Defaults to False. (optional)
    :param string ca_cert: SSL CA bundle file to use. (optional)
    :param integer retries: How many times idempotent (GET, PUT, DELETE)
                            requests to Tacker server should be retried if
                            they fail (default: 0).
    :param bool raise_errors: If True then exceptions caused by connection
                              failure are propagated to the caller.
                              (default: True)
    :param session: Keystone client auth session to use. (optional)
    :param auth: Keystone auth plugin to use. (optional)

    Example::

        from tackerclient.v1_0 import client
        tacker = client.Client(username=USER,
                                password=PASS,
                                tenant_name=TENANT_NAME,
                                auth_url=KEYSTONE_URL)

        nets = tacker.list_networks()
        ...

    """

    # API has no way to report plurals, so we have to hard code them
    # This variable should be overridden by a child class.
    EXTED_PLURALS = {}

    def __init__(self, **kwargs):
        """Initialize a new client for the Tacker v1.0 API."""
        super(ClientBase, self).__init__()
        self.retries = kwargs.pop('retries', 0)
        self.raise_errors = kwargs.pop('raise_errors', True)
        self.httpclient = client.construct_http_client(**kwargs)
        self.version = '1.0'
        self.format = 'json'
        self.action_prefix = "/v%s" % (self.version)
        self.retry_interval = 1

    def _handle_fault_response(self, status_code, response_body):
        # Create exception with HTTP status code and message
        _logger.debug("Error message: %s", response_body)
        # Add deserialized error message to exception arguments
        try:
            des_error_body = self.deserialize(response_body, status_code)
        except Exception:
            # If unable to deserialized body it is probably not a
            # Tacker error
            des_error_body = {'message': response_body}
        # Raise the appropriate exception
        exception_handler_v10(status_code, des_error_body)

    def do_request(self, method, action, body=None, headers=None, params=None):
        # Add format and tenant_id
        action += ".%s" % self.format
        action = self.action_prefix + action
        if type(params) is dict and params:
            params = utils.safe_encode_dict(params)
            action += '?' + urlparse.urlencode(params, doseq=1)

        if body:
            body = self.serialize(body)

        resp, replybody = self.httpclient.do_request(
            action, method, body=body,
            content_type=self.content_type())

        status_code = resp.status_code
        if status_code in (requests.codes.ok,
                           requests.codes.created,
                           requests.codes.accepted,
                           requests.codes.no_content):
            return self.deserialize(replybody, status_code)
        else:
            if not replybody:
                replybody = resp.reason
            self._handle_fault_response(status_code, replybody)

    def get_auth_info(self):
        return self.httpclient.get_auth_info()

    def serialize(self, data):
        """Serializes a dictionary into either XML or JSON.

        A dictionary with a single key can be passed and it can contain any
        structure.
        """
        if data is None:
            return None
        elif type(data) is dict:
            return serializer.Serializer(
                self.get_attr_metadata()).serialize(data, self.content_type())
        else:
            raise Exception(_("Unable to serialize object of type = '%s'") %
                            type(data))

    def deserialize(self, data, status_code):
        """Deserializes an XML or JSON string into a dictionary."""
        if status_code == 204:
            return data
        return serializer.Serializer(self.get_attr_metadata()).deserialize(
            data, self.content_type())['body']

    def get_attr_metadata(self):
        if self.format == 'json':
            return {}
        old_request_format = self.format
        self.format = 'json'
        exts = self.list_extensions()['extensions']
        self.format = old_request_format
        ns = dict([(ext['alias'], ext['namespace']) for ext in exts])
        self.EXTED_PLURALS.update(constants.PLURALS)
        return {'plurals': self.EXTED_PLURALS,
                'xmlns': constants.XML_NS_V10,
                constants.EXT_NS: ns}

    def content_type(self, _format=None):
        """Returns the mime-type for either 'xml' or 'json'.

        Defaults to the currently set format.
        """
        _format = _format or self.format
        return "application/%s" % (_format)

    def retry_request(self, method, action, body=None,
                      headers=None, params=None):
        """Call do_request with the default retry configuration.

        Only idempotent requests should retry failed connection attempts.
        :raises: ConnectionFailed if the maximum # of retries is exceeded
        """
        max_attempts = self.retries + 1
        for i in range(max_attempts):
            try:
                return self.do_request(method, action, body=body,
                                       headers=headers, params=params)
            except exceptions.ConnectionFailed:
                # Exception has already been logged by do_request()
                if i < self.retries:
                    _logger.debug('Retrying connection to Tacker service')
                    time.sleep(self.retry_interval)
                elif self.raise_errors:
                    raise

        if self.retries:
            msg = (_("Failed to connect to Tacker server after %d attempts")
                   % max_attempts)
        else:
            msg = _("Failed to connect Tacker server")

        raise exceptions.ConnectionFailed(reason=msg)

    def delete(self, action, body=None, headers=None, params=None):
        return self.retry_request("DELETE", action, body=body,
                                  headers=headers, params=params)

    def get(self, action, body=None, headers=None, params=None):
        return self.retry_request("GET", action, body=body,
                                  headers=headers, params=params)

    def post(self, action, body=None, headers=None, params=None):
        # Do not retry POST requests to avoid the orphan objects problem.
        return self.do_request("POST", action, body=body,
                               headers=headers, params=params)

    def put(self, action, body=None, headers=None, params=None):
        return self.retry_request("PUT", action, body=body,
                                  headers=headers, params=params)

    def list(self, collection, path, retrieve_all=True, **params):
        if retrieve_all:
            res = []
            for r in self._pagination(collection, path, **params):
                res.extend(r[collection])
            return {collection: res}
        else:
            return self._pagination(collection, path, **params)

    def _pagination(self, collection, path, **params):
        if params.get('page_reverse', False):
            linkrel = 'previous'
        else:
            linkrel = 'next'
        next = True
        while next:
            res = self.get(path, params=params)
            yield res
            next = False
            try:
                for link in res['%s_links' % collection]:
                    if link['rel'] == linkrel:
                        query_str = urlparse.urlparse(link['href']).query
                        params = urlparse.parse_qs(query_str)
                        next = True
                        break
            except KeyError:
                break


class Client(ClientBase):

    extensions_path = "/extensions"
    extension_path = "/extensions/%s"

    vnfds_path = '/vnfds'
    vnfd_path = '/vnfds/%s'
    vnfs_path = '/vnfs'
    vnf_path = '/vnfs/%s'
    vnf_scale_path = '/vnfs/%s/actions'
    vnf_resources_path = '/vnfs/%s/resources'

    vims_path = '/vims'
    vim_path = '/vims/%s'

    events_path = '/events'
    event_path = '/events/%s'

    vnffgds_path = '/vnffgds'
    vnffgd_path = '/vnffgds/%s'

    vnffgs_path = '/vnffgs'
    vnffg_path = '/vnffgs/%s'

    nfps_path = '/nfps'
    nfp_path = '/nfps/%s'

    sfcs_path = '/sfcs'
    sfc_path = '/sfcs/%s'

    fcs_path = '/classifiers'
    fc_path = '/classifiers/%s'

    nsds_path = '/nsds'
    nsd_path = '/nsds/%s'

    nss_path = '/nss'
    ns_path = '/nss/%s'

    clusters_path = '/clusters'
    cluster_path = '/clusters/%s'
    cluster_members_path = '/clustermembers'
    cluster_member_path = '/clustermembers/%s'

    # API has no way to report plurals, so we have to hard code them
    # EXTED_PLURALS = {}

    @APIParamsCall
    def list_extensions(self, **_params):
        """Fetch a list of all exts on server side."""
        return self.get(self.extensions_path, params=_params)

    @APIParamsCall
    def show_extension(self, ext_alias, **_params):
        """Fetch a list of all exts on server side."""
        return self.get(self.extension_path % ext_alias, params=_params)

    _VNFD = "vnfd"
    _NSD = "nsd"

    @APIParamsCall
    def list_vnfds(self, retrieve_all=True, **_params):
        vnfds_dict = self.list(self._VNFD + 's',
                               self.vnfds_path,
                               retrieve_all,
                               **_params)
        for vnfd in vnfds_dict['vnfds']:
            if vnfd.get('description'):
                if len(vnfd['description']) > DEFAULT_DESC_LENGTH:
                    vnfd['description'] = \
                        vnfd['description'][:DEFAULT_DESC_LENGTH]
                    vnfd['description'] += '...'
        return vnfds_dict

    @APIParamsCall
    def show_vnfd(self, vnfd, **_params):
        return self.get(self.vnfd_path % vnfd,
                        params=_params)

    @APIParamsCall
    def create_vnfd(self, body):
        body[self._VNFD]['service_types'] = [{'service_type': 'vnfd'}]
        return self.post(self.vnfds_path, body)

    @APIParamsCall
    def delete_vnfd(self, vnfd):
        return self.delete(self.vnfd_path % vnfd)

    @APIParamsCall
    def list_vnfs(self, retrieve_all=True, **_params):
        vnfs = self.list('vnfs', self.vnfs_path, retrieve_all, **_params)
        for vnf in vnfs['vnfs']:
            error_reason = vnf.get('error_reason', None)
            if error_reason and \
                len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                vnf['error_reason'] = error_reason[
                    :DEFAULT_ERROR_REASON_LENGTH]
                vnf['error_reason'] += '...'
        return vnfs

    @APIParamsCall
    def show_vnf(self, vnf, **_params):
        return self.get(self.vnf_path % vnf, params=_params)

    @APIParamsCall
    def create_vnf(self, body):
        return self.post(self.vnfs_path, body=body)

    @APIParamsCall
    def delete_vnf(self, vnf):
        return self.delete(self.vnf_path % vnf)

    @APIParamsCall
    def update_vnf(self, vnf, body):
        return self.put(self.vnf_path % vnf, body=body)

    @APIParamsCall
    def list_vnf_resources(self, vnf, retrieve_all=True, **_params):
        return self.list('resources', self.vnf_resources_path % vnf,
                         retrieve_all, **_params)

    @APIParamsCall
    def scale_vnf(self, vnf, body=None):
        return self.post(self.vnf_scale_path % vnf, body=body)

    @APIParamsCall
    def show_vim(self, vim, **_params):
        return self.get(self.vim_path % vim, params=_params)

    _VIM = "vim"

    @APIParamsCall
    def create_vim(self, body):
        return self.post(self.vims_path, body=body)

    @APIParamsCall
    def delete_vim(self, vim):
        return self.delete(self.vim_path % vim)

    @APIParamsCall
    def update_vim(self, vim, body):
        return self.put(self.vim_path % vim, body=body)

    @APIParamsCall
    def list_vims(self, retrieve_all=True, **_params):
        return self.list('vims', self.vims_path, retrieve_all, **_params)

    @APIParamsCall
    def list_events(self, retrieve_all=True, **_params):
        events = self.list('events', self.events_path, retrieve_all,
                           **_params)
        return events

    @APIParamsCall
    def list_vnf_events(self, retrieve_all=True, **_params):
        _params['resource_type'] = 'vnf'
        events = self.list('events', self.events_path, retrieve_all,
                           **_params)
        vnf_events = {}
        vnf_events['vnf_events'] = events['events']
        return vnf_events

    @APIParamsCall
    def list_vnfd_events(self, retrieve_all=True, **_params):
        _params['resource_type'] = 'vnfd'
        events = self.list('events', self.events_path, retrieve_all,
                           **_params)
        vnfd_events = {}
        vnfd_events['vnfd_events'] = events['events']
        return vnfd_events

    @APIParamsCall
    def list_vim_events(self, retrieve_all=True, **_params):
        _params['resource_type'] = 'vim'
        events = self.list('events', self.events_path, retrieve_all,
                           **_params)
        vim_events = {}
        vim_events['vim_events'] = events['events']
        return vim_events

    @APIParamsCall
    def show_event(self, event_id, **_params):
        return self.get(self.event_path % event_id, params=_params)

    _VNFFGD = "vnffgd"

    @APIParamsCall
    def create_vnffgd(self, body):
        return self.post(self.vnffgds_path, body)

    @APIParamsCall
    def list_vnffgds(self, retrieve_all=True, **_params):
        vnffgds_dict = self.list(self._VNFFGD + 's',
                                 self.vnffgds_path,
                                 retrieve_all,
                                 **_params)
        for vnffgd in vnffgds_dict['vnffgds']:
            if 'description' in vnffgd.keys() and \
                len(vnffgd['description']) > DEFAULT_DESC_LENGTH:
                vnffgd['description'] = vnffgd['description'][
                    :DEFAULT_DESC_LENGTH]
                vnffgd['description'] += '...'
        return vnffgds_dict

    @APIParamsCall
    def show_vnffgd(self, vnffgd, **_params):
        return self.get(self.vnffgd_path % vnffgd, params=_params)

    @APIParamsCall
    def delete_vnffgd(self, vnffgd):
        return self.delete(self.vnffgd_path % vnffgd)

    @APIParamsCall
    def list_vnffgs(self, retrieve_all=True, **_params):
        vnffgs = self.list('vnffgs', self.vnffgs_path, retrieve_all, **_params)
        for vnffg in vnffgs['vnffgs']:
            error_reason = vnffg.get('error_reason', None)
            if error_reason and \
                    len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                vnffg['error_reason'] = error_reason[
                    :DEFAULT_ERROR_REASON_LENGTH]
                vnffg['error_reason'] += '...'
        return vnffgs

    @APIParamsCall
    def show_vnffg(self, vnffg, **_params):
        return self.get(self.vnffg_path % vnffg, params=_params)

    @APIParamsCall
    def create_vnffg(self, body):
        return self.post(self.vnffgs_path, body=body)

    @APIParamsCall
    def delete_vnffg(self, vnffg):
        return self.delete(self.vnffg_path % vnffg)

    @APIParamsCall
    def update_vnffg(self, vnffg, body):
        return self.put(self.vnffg_path % vnffg, body=body)

    @APIParamsCall
    def list_sfcs(self, retrieve_all=True, **_params):
        sfcs = self.list('sfcs', self.sfcs_path, retrieve_all, **_params)
        for chain in sfcs['sfcs']:
            error_reason = chain.get('error_reason', None)
            if error_reason and \
                    len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                chain['error_reason'] = error_reason[
                    :DEFAULT_ERROR_REASON_LENGTH]
                chain['error_reason'] += '...'
        return sfcs

    @APIParamsCall
    def show_sfc(self, chain, **_params):
        return self.get(self.sfc_path % chain, params=_params)

    @APIParamsCall
    def list_nfps(self, retrieve_all=True, **_params):
        nfps = self.list('nfps', self.nfps_path, retrieve_all, **_params)
        for nfp in nfps['nfps']:
            error_reason = nfp.get('error_reason', None)
            if error_reason and \
                    len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                nfp['error_reason'] = error_reason[
                    :DEFAULT_ERROR_REASON_LENGTH]
                nfp['error_reason'] += '...'
        return nfps

    @APIParamsCall
    def show_nfp(self, nfp, **_params):
        return self.get(self.nfp_path % nfp, params=_params)

    @APIParamsCall
    def list_classifiers(self, retrieve_all=True, **_params):
        classifiers = self.list('classifiers', self.fcs_path, retrieve_all,
                                **_params)
        for classifier in classifiers['classifiers']:
            error_reason = classifier.get('error_reason', None)
            if error_reason and \
                    len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                classifier['error_reason'] = error_reason[
                    :DEFAULT_ERROR_REASON_LENGTH]
                classifier['error_reason'] += '...'
        return classifiers

    @APIParamsCall
    def show_classifier(self, classifier, **_params):
        return self.get(self.fc_path % classifier, params=_params)

    @APIParamsCall
    def list_nsds(self, retrieve_all=True, **_params):
        nsds_dict = self.list(self._NSD + 's',
                              self.nsds_path,
                              retrieve_all,
                              **_params)
        for nsd in nsds_dict['nsds']:
            if 'description' in nsd.keys() and \
                len(nsd['description']) > DEFAULT_DESC_LENGTH:
                nsd['description'] = nsd['description'][:DEFAULT_DESC_LENGTH]
                nsd['description'] += '...'
        return nsds_dict

    @APIParamsCall
    def show_nsd(self, nsd, **_params):
        return self.get(self.nsd_path % nsd,
                        params=_params)

    @APIParamsCall
    def create_nsd(self, body):
        return self.post(self.nsds_path, body)

    @APIParamsCall
    def delete_nsd(self, nsd):
        return self.delete(self.nsd_path % nsd)

    @APIParamsCall
    def list_nss(self, retrieve_all=True, **_params):
        nss = self.list('nss', self.nss_path, retrieve_all, **_params)
        for ns in nss['nss']:
            error_reason = ns.get('error_reason', None)
            if error_reason and \
                len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                ns['error_reason'] = error_reason[
                    :DEFAULT_ERROR_REASON_LENGTH]
                ns['error_reason'] += '...'
        return nss

    @APIParamsCall
    def show_ns(self, ns, **_params):
        return self.get(self.ns_path % ns, params=_params)

    @APIParamsCall
    def create_ns(self, body):
        return self.post(self.nss_path, body=body)

    @APIParamsCall
    def delete_ns(self, ns):
        return self.delete(self.ns_path % ns)

    @APIParamsCall
    def create_cluster(self, body=None):
        return self.post(self.clusters_path, body)

    @APIParamsCall
    def list_clusters(self, retrieve_all=True, **_params):
        clusters = self.list('clusters', self.clusters_path,
                             retrieve_all, **_params)
        return clusters

    @APIParamsCall
    def show_cluster(self, cluster, **_params):
        member = self.get(self.cluster_path % cluster,
                          params=_params)
        return member

    @APIParamsCall
    def delete_cluster(self, cluster):
        return self.delete(self.cluster_path % cluster)

    @APIParamsCall
    def create_clustermember(self, body=None):
        return self.post(self.cluster_members_path, body)

    @APIParamsCall
    def list_clustermembers(self, retrieve_all=True, **_params):
        cluster_members = self.list('clustermembers',
                                    self.cluster_members_path,
                                    retrieve_all, **_params)
        return cluster_members

    @APIParamsCall
    def show_clustermember(self, clustermember, **_params):
        member = self.get(self.cluster_member_path % clustermember,
                          params=_params)
        return member

    @APIParamsCall
    def delete_clustermember(self, clustermember):
        return self.delete(self.cluster_member_path % clustermember)
