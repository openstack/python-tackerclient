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
import re
import time

import requests
from urllib import parse as urlparse

from tackerclient import client
from tackerclient.common import exceptions
from tackerclient.common import serializer
from tackerclient.common import utils
from tackerclient.i18n import _

_logger = logging.getLogger(__name__)
DEFAULT_DESC_LENGTH = 25
DEFAULT_ERROR_REASON_LENGTH = 100
STATUS_CODE_MAP = {
    400: "badRequest",
    401: "unauthorized",
    403: "forbidden",
    404: "itemNotFound",
    405: "badMethod",
    409: "conflictingRequest",
    413: "overLimit",
    415: "badMediaType",
    429: "overLimit",
    501: "notImplemented",
    503: "serviceUnavailable"}


def exception_handler_v10(status_code, error_content):
    """Exception handler for API v1.0 client.

    This routine generates the appropriate Tacker exception according to
    the contents of the response body.

    :param status_code: HTTP error status code
    :param error_content: deserialized body of error response
    """
    etsi_error_content = error_content
    error_dict = None
    if isinstance(error_content, dict):
        error_dict = error_content.get('TackerError')
        if not error_dict:
            error_content = error_content.get(STATUS_CODE_MAP.get(status_code),
                                              'tackerFault')
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
        # ETSI error response
        if isinstance(etsi_error_content, dict):
            if etsi_error_content.get('status') and \
                etsi_error_content.get('detail'):
                message = etsi_error_content.get('detail')
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
        self.rel = None
        self.params = None
        self.accept = None

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

    def build_action(self, action):
        action += ".%s" % self.format
        action = self.action_prefix + action
        return action

    def _build_params_query(self, params=None):
        flag_params = []
        keyval_params = {}
        for key, value in params.items():
            if value is None:
                flag_params.append(key)
            else:
                keyval_params[key] = value

        flags_encoded = utils.safe_encode_list(flag_params) \
            if flag_params else ""
        keyval_encoded = utils.safe_encode_dict(keyval_params) \
            if keyval_params else ""

        query = ""
        for flag in flags_encoded:
            query = query + urlparse.quote_plus(flag) + '&'
        query = query + urlparse.urlencode(keyval_encoded, doseq=1)
        return query.strip('&')

    def do_request(self, method, action, body=None, headers=None, params=None):
        action = self.build_action(action)
        # Add format and tenant_id
        if type(params) is dict and params:
            query = self._build_params_query(params)
            action += '?' + query

        if body or body == {}:
            body = self.serialize(body)

        if headers is None:
            # self.httpclient.do_request is not accept 'headers=None'.
            headers = {}

        resp, replybody = self.httpclient.do_request(
            action, method, body=body, headers=headers,
            content_type=self.content_type(), accept=self.accept)

        if 'application/zip' == resp.headers.get('Content-Type'):
            self.format = 'zip'
        elif 'text/plain' == resp.headers.get('Content-Type'):
            self.format = 'text'
        elif 'artifacts' in action:
            self.format = 'any'
        else:
            self.format = 'json'

        url = None
        rel = None

        link = resp.headers.get('Link', None)
        if link is not None:
            url = re.findall('<(.*)>', link)[0]
            rel = re.findall('rel="(.*)"', link)[0]

        if rel == 'next':
            self.rel = 'next'
            query_str = urlparse.urlparse(url).query
            self.params = urlparse.parse_qs(query_str)

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
        """Serializes a dictionary JSON.

        A dictionary with a single key can be passed and it can contain any
        structure.
        """
        if data is None:
            return None
        elif self.format in ('zip', 'text'):
            return data
        elif type(data) is dict:
            return serializer.Serializer().serialize(data, 'application/json')
        else:
            raise Exception(_("Unable to serialize object of type = '%s'") %
                            type(data))

    def deserialize(self, data, status_code):
        """Deserializes an JSON string into a dictionary."""
        if status_code in (204, 202) or self.format in ('zip', 'text', 'any'):
            return data
        return serializer.Serializer().deserialize(
            data, 'application/json')['body']

    def content_type(self, _format=None):
        """Returns the mime-type for either 'json, 'text', or 'zip'.

        Defaults to the currently set format.
        """
        _format = _format or self.format
        if self.format == 'text':
            return "text/plain"
        elif self.format == 'both':
            return "text/plain,application/zip"
        else:
            return "application/%s" % (_format)

    def retry_request(self, method, action, body=None,
                      headers=None, params=None):
        """Call do_request with the default retry configuration.

        Only idempotent requests should retry failed connection attempts.
        :raises ConnectionFailed: if the maximum # of retries is exceeded
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

    def patch(self, action, body=None, headers=None, params=None):
        self.format = 'merge-patch+json'
        self.accept = 'json'
        return self.retry_request("PATCH", action, body=body,
                                  headers=headers, params=params)

    def list(self, collection, path, retrieve_all=True, headers=None,
             **params):
        if retrieve_all:
            res = []
            for r in self._pagination(collection, path, headers, **params):
                if type(r) is list:
                    res.extend(r)
                else:
                    res.extend(r[collection])
            return {collection: res} if collection else res
        else:
            return self._pagination(collection, path, headers, **params)

    def _pagination(self, collection, path, headers, **params):
        if params.get('page_reverse', False):
            linkrel = 'previous'
        else:
            linkrel = 'next'
        next = True
        while next:
            self.rel = None
            res = self.get(path, headers=headers, params=params)
            yield res
            next = False
            try:
                if type(res) is list:
                    if self.rel == 'next':
                        params = self.params
                        next = True

                else:
                    for link in res['%s_links' % collection]:
                        if link['rel'] == linkrel:
                            query_str = urlparse.urlparse(link['href']).query
                            params = urlparse.parse_qs(query_str)
                            next = True
                            break
            except KeyError:
                break


class LegacyClient(ClientBase):

    vims_path = '/vims'
    vim_path = '/vims/%s'

    # API has no way to report plurals, so we have to hard code them
    # EXTED_PLURALS = {}

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


class VnfPackageClient(ClientBase):
    """Client for vnfpackage APIs.

    Purpose of this class is to create required request url for vnfpackage
    APIs.
    """

    vnfpackages_path = '/vnfpkgm/v1/vnf_packages'
    vnfpackage_path = '/vnfpkgm/v1/vnf_packages/%s'
    vnfpackage_vnfd_path = '/vnfpkgm/v1/vnf_packages/%s/vnfd'
    vnfpackage_download_path = '/vnfpkgm/v1/vnf_packages/%s/package_content'
    vnfpakcage_artifact_path = '/vnfpkgm/v1/vnf_packages/%(id)s/artifacts/' \
                               '%(artifact_path)s'

    def build_action(self, action):
        return action

    @APIParamsCall
    def create_vnf_package(self, body):
        return self.post(self.vnfpackages_path, body=body)

    @APIParamsCall
    def list_vnf_packages(self, retrieve_all=True, **_params):
        vnf_packages = self.list("vnf_packages", self.vnfpackages_path,
                                 retrieve_all, **_params)
        return vnf_packages

    @APIParamsCall
    def show_vnf_package(self, vnf_package, **_params):
        return self.get(self.vnfpackage_path % vnf_package, params=_params)

    @APIParamsCall
    def delete_vnf_package(self, vnf_package):
        return self.delete(self.vnfpackage_path % vnf_package)

    @APIParamsCall
    def upload_vnf_package(self, vnf_package, file_data=None, **attrs):
        if attrs.get('url'):
            json = {'addressInformation': attrs.get('url')}
            for key in ['userName', 'password']:
                if attrs.get(key):
                    json.update({key: attrs.get(key)})
            return self.post(
                '{base_path}/{id}/package_content/upload_from_uri'.format(
                    id=vnf_package, base_path=self.vnfpackages_path),
                body=json)
        else:
            self.format = 'zip'
            self.accept = 'json'
            return self.put('{base_path}/{id}/package_content'.format(
                id=vnf_package,
                base_path=self.vnfpackages_path),
                body=file_data)

    @APIParamsCall
    def download_vnf_package(self, vnf_package):
        self.format = 'zip'
        return self.get(self.vnfpackage_download_path % vnf_package)

    @APIParamsCall
    def download_vnfd_from_vnf_package(self, vnf_package, accept):
        """Read VNFD of an on-boarded VNF Package.

        :param vnf_package: The value can be either the ID of a vnf package
                            or a :class:`~openstack.nfv_orchestration.v1.
                            vnf_package` instance.
        :param accept: Valid values are 'text/plain', 'application/zip' and
                       'both'. According to these values 'Accept' header will
                        be set as 'text/plain', 'application/zip',
                       'text/plain,application/zip' respectively.

        :returns: If the VNFD is implemented in the form of multiple files,
                  a ZIP file embedding these files shall be returned.
                  If the VNFD is implemented as a single file, either that
                  file or a ZIP file embedding that file shall be returned.
        """
        if accept == 'text/plain':
            self.format = 'text'
        elif accept == 'application/zip':
            self.format = 'zip'
        else:
            self.format = 'both'
        return self.get(self.vnfpackage_vnfd_path % vnf_package)

    @APIParamsCall
    def download_artifact_from_vnf_package(self, vnf_package, artifact_path):
        return self.get(self.vnfpakcage_artifact_path %
                        {'id': vnf_package, 'artifact_path': artifact_path})

    @APIParamsCall
    def update_vnf_package(self, vnf_package, body):
        return self.patch(self.vnfpackage_path % vnf_package, body=body)


class VnfLCMClient(ClientBase):
    """Client for vnflcm APIs.

    Purpose of this class is to create required request url for vnflcm
    APIs.
    """

    def __init__(self, api_version, **kwargs):
        super(VnfLCMClient, self).__init__(**kwargs)
        self.headers = {'Version': '1.3.0'}
        sol_api_version = 'v1'
        if api_version == '2':
            self.headers = {'Version': '2.0.0'}
            sol_api_version = 'v2'

        self.vnf_instances_path = (
            '/vnflcm/{}/vnf_instances'.format(sol_api_version))
        self.vnf_instance_path = (
            '/vnflcm/{}/vnf_instances/%s'.format(sol_api_version))
        self.vnf_lcm_op_occurrences_path = (
            '/vnflcm/{}/vnf_lcm_op_occs'.format(sol_api_version))
        self.vnf_lcm_op_occs_path = (
            '/vnflcm/{}/vnf_lcm_op_occs/%s'.format(sol_api_version))
        self.lccn_subscriptions_path = (
            '/vnflcm/{}/subscriptions'.format(sol_api_version))
        self.lccn_subscription_path = (
            '/vnflcm/{}/subscriptions/%s'.format(sol_api_version))

    def build_action(self, action):
        return action

    @APIParamsCall
    def create_vnf_instance(self, body):
        return self.post(self.vnf_instances_path, body=body,
                         headers=self.headers)

    @APIParamsCall
    def show_vnf_instance(self, vnf_id, **_params):
        return self.get(self.vnf_instance_path % vnf_id,
                        headers=self.headers, params=_params)

    @APIParamsCall
    def list_vnf_instances(self, retrieve_all=True, **_params):
        vnf_instances = self.list(None, self.vnf_instances_path,
                                  retrieve_all, headers=self.headers,
                                  **_params)
        return vnf_instances

    @APIParamsCall
    def instantiate_vnf_instance(self, vnf_id, body):
        return self.post((self.vnf_instance_path + "/instantiate") % vnf_id,
                         body=body, headers=self.headers)

    @APIParamsCall
    def heal_vnf_instance(self, vnf_id, body):
        return self.post((self.vnf_instance_path + "/heal") % vnf_id,
                         body=body, headers=self.headers)

    @APIParamsCall
    def terminate_vnf_instance(self, vnf_id, body):
        return self.post((self.vnf_instance_path + "/terminate") % vnf_id,
                         body=body, headers=self.headers)

    @APIParamsCall
    def delete_vnf_instance(self, vnf_id):
        return self.delete(self.vnf_instance_path % vnf_id,
                           headers=self.headers)

    @APIParamsCall
    def update_vnf_instance(self, vnf_id, body):
        return self.patch(self.vnf_instance_path % vnf_id, body=body,
                          headers=self.headers)

    @APIParamsCall
    def scale_vnf_instance(self, vnf_id, body):
        return self.post((self.vnf_instance_path + "/scale") % vnf_id,
                         body=body, headers=self.headers)

    @APIParamsCall
    def rollback_vnf_instance(self, occ_id):
        return self.post((self.vnf_lcm_op_occs_path + "/rollback") % occ_id,
                         headers=self.headers)

    @APIParamsCall
    def cancel_vnf_instance(self, occ_id, body):
        return self.post((self.vnf_lcm_op_occs_path + "/cancel") % occ_id,
                         body=body)

    @APIParamsCall
    def fail_vnf_instance(self, occ_id):
        return self.post((self.vnf_lcm_op_occs_path + "/fail") % occ_id,
                         headers=self.headers)

    @APIParamsCall
    def change_ext_conn_vnf_instance(self, vnf_id, body):
        return self.post((self.vnf_instance_path + "/change_ext_conn") %
                         vnf_id, body=body, headers=self.headers)

    @APIParamsCall
    def change_vnfpkg_vnf_instance(self, vnf_id, body):
        # NOTE: it is only supported by V2-API.
        if self.vnf_instance_path.split('/')[2] == 'v2':
            return self.post((self.vnf_instance_path + "/change_vnfpkg") %
                             vnf_id, body=body, headers=self.headers)
        else:
            raise exceptions.UnsupportedCommandVersion(version='1')

    @APIParamsCall
    def retry_vnf_instance(self, occ_id):
        return self.post((self.vnf_lcm_op_occs_path + "/retry") % occ_id,
                         headers=self.headers)

    @APIParamsCall
    def list_vnf_lcm_op_occs(self, retrieve_all=True, **_params):
        vnf_lcm_op_occs = self.list(None, self.vnf_lcm_op_occurrences_path,
                                    retrieve_all, headers=self.headers,
                                    **_params)
        return vnf_lcm_op_occs

    @APIParamsCall
    def show_vnf_lcm_op_occs(self, occ_id):
        return self.get(self.vnf_lcm_op_occs_path % occ_id,
                        headers=self.headers)

    @APIParamsCall
    def create_lccn_subscription(self, body):
        return self.post(self.lccn_subscriptions_path, body=body,
                         headers=self.headers)

    @APIParamsCall
    def delete_lccn_subscription(self, subsc_id):
        return self.delete(self.lccn_subscription_path % subsc_id,
                           headers=self.headers)

    @APIParamsCall
    def list_lccn_subscriptions(self, retrieve_all=True, **_params):
        subscriptions = self.list(None, self.lccn_subscriptions_path,
                                  retrieve_all, headers=self.headers,
                                  **_params)
        return subscriptions

    @APIParamsCall
    def show_lccn_subscription(self, subsc_id):
        return self.get(self.lccn_subscription_path % subsc_id,
                        headers=self.headers)

    @APIParamsCall
    def show_vnf_lcm_versions(self, major_version):
        if major_version is None:
            path = "/vnflcm/api_versions"
        else:
            path = "/vnflcm/{}/api_versions".format(major_version)
        # NOTE: This may be called with any combination of
        # --os-tacker-api-verson:[1, 2] and major_version:[None, 1, 2].
        # Specifying "headers={'Version': '2.0.0'}" is most simple to
        # make all cases OK.
        return self.get(path, headers={'Version': '2.0.0'})


class VnfFMClient(ClientBase):
    headers = {'Version': '1.3.0'}
    vnf_fm_alarms_path = '/vnffm/v1/alarms'
    vnf_fm_alarm_path = '/vnffm/v1/alarms/%s'
    vnf_fm_subs_path = '/vnffm/v1/subscriptions'
    vnf_fm_sub_path = '/vnffm/v1/subscriptions/%s'

    def build_action(self, action):
        return action

    @APIParamsCall
    def list_vnf_fm_alarms(self, retrieve_all=True, **_params):
        vnf_fm_alarms = self.list(
            "vnf_fm_alarms", self.vnf_fm_alarms_path, retrieve_all,
            headers=self.headers, **_params)
        return vnf_fm_alarms

    @APIParamsCall
    def show_vnf_fm_alarm(self, vnf_fm_alarm_id):
        return self.get(
            self.vnf_fm_alarm_path % vnf_fm_alarm_id, headers=self.headers)

    @APIParamsCall
    def update_vnf_fm_alarm(self, vnf_fm_alarm_id, body):
        return self.patch(
            self.vnf_fm_alarm_path % vnf_fm_alarm_id, body=body,
            headers=self.headers)

    @APIParamsCall
    def create_vnf_fm_sub(self, body):
        return self.post(
            self.vnf_fm_subs_path, body=body, headers=self.headers)

    @APIParamsCall
    def list_vnf_fm_subs(self, retrieve_all=True, **_params):
        vnf_fm_subs = self.list("vnf_fm_subs", self.vnf_fm_subs_path,
                                retrieve_all, headers=self.headers, **_params)
        return vnf_fm_subs

    @APIParamsCall
    def show_vnf_fm_sub(self, vnf_fm_sub_id):
        return self.get(
            self.vnf_fm_sub_path % vnf_fm_sub_id, headers=self.headers)

    @APIParamsCall
    def delete_vnf_fm_sub(self, vnf_fm_sub_id):
        return self.delete(
            self.vnf_fm_sub_path % vnf_fm_sub_id, headers=self.headers)


class VnfPMClient(ClientBase):
    headers = {'Version': '2.1.0'}
    vnf_pm_jobs_path = '/vnfpm/v2/pm_jobs'
    vnf_pm_job_path = '/vnfpm/v2/pm_jobs/%s'
    vnf_pm_reports_path = '/vnfpm/v2/pm_jobs/%(job_id)s/reports/%(report_id)s'
    vnf_pm_thresholds_path = '/vnfpm/v2/thresholds'
    vnf_pm_threshold_path = '/vnfpm/v2/thresholds/%s'

    def build_action(self, action):
        return action

    @APIParamsCall
    def create_vnf_pm_job(self, body):
        return self.post(
            self.vnf_pm_jobs_path, body=body, headers=self.headers)

    @APIParamsCall
    def list_vnf_pm_jobs(self, retrieve_all=True, **_params):
        vnf_pm_jobs = self.list(
            "vnf_pm_jobs", self.vnf_pm_jobs_path, retrieve_all,
            headers=self.headers, **_params)
        return vnf_pm_jobs

    @APIParamsCall
    def show_vnf_pm_job(self, vnf_pm_job_id):
        return self.get(
            self.vnf_pm_job_path % vnf_pm_job_id, headers=self.headers)

    @APIParamsCall
    def update_vnf_pm_job(self, vnf_pm_job_id, body):
        return self.patch(
            self.vnf_pm_job_path % vnf_pm_job_id, body=body,
            headers=self.headers)

    @APIParamsCall
    def delete_vnf_pm_job(self, vnf_pm_job_id):
        return self.delete(
            self.vnf_pm_job_path % vnf_pm_job_id, headers=self.headers)

    @APIParamsCall
    def show_vnf_pm_report(self, vnf_pm_job_id, vnf_pm_report_id):
        return self.get(
            self.vnf_pm_reports_path % {
                'job_id': vnf_pm_job_id, 'report_id': vnf_pm_report_id
            }, headers=self.headers)

    @APIParamsCall
    def create_vnf_pm_threshold(self, body):
        return self.post(
            self.vnf_pm_thresholds_path, body=body, headers=self.headers)

    @APIParamsCall
    def list_vnf_pm_thresholds(self, retrieve_all=True, **_params):
        return self.list(
            "vnf_pm_thresholds", self.vnf_pm_thresholds_path, retrieve_all,
            headers=self.headers, **_params)

    @APIParamsCall
    def show_vnf_pm_threshold(self, vnf_pm_threshold_id):
        return self.get(
            self.vnf_pm_threshold_path % vnf_pm_threshold_id,
            headers=self.headers)

    @APIParamsCall
    def update_vnf_pm_threshold(self, vnf_pm_threshold_id, body):
        return self.patch(
            self.vnf_pm_threshold_path % vnf_pm_threshold_id, body=body,
            headers=self.headers)

    @APIParamsCall
    def delete_vnf_pm_threshold(self, vnf_pm_threshold_id):
        return self.delete(
            self.vnf_pm_threshold_path % vnf_pm_threshold_id,
            headers=self.headers)


class Client(object):
    """Unified interface to interact with multiple apps of tacker service.

    This class is a single entry point to interact with legacy tacker apis and
    vnf packages apis.

        Example::

        from tackerclient.v1_0 import client
        tacker = client.Client(username=USER,
                                password=PASS,
                                tenant_name=TENANT_NAME,
                                auth_url=KEYSTONE_URL)

        vnf_package = tacker.create_vnf_package(...)
        nsd = tacker.create_nsd(...)

    """

    def __init__(self, **kwargs):
        api_version = kwargs.pop('api_version', '1')
        self.vnf_lcm_client = VnfLCMClient(api_version, **kwargs)
        self.vnf_fm_client = VnfFMClient(**kwargs)
        self.vnf_pm_client = VnfPMClient(**kwargs)
        self.vnf_package_client = VnfPackageClient(**kwargs)
        self.legacy_client = LegacyClient(**kwargs)

    # LegacyClient methods

    def delete(self, action, body=None, headers=None, params=None):
        return self.legacy_client.delete(action, body=body, headers=headers,
                                         params=params)

    def get(self, action, body=None, headers=None, params=None):
        return self.legacy_client.get(action, body=body, headers=headers,
                                      params=params)

    def post(self, action, body=None, headers=None, params=None):
        return self.legacy_client.post(action, body=body, headers=headers,
                                       params=params)

    def put(self, action, body=None, headers=None, params=None):
        return self.legacy_client.put(action, body=body, headers=headers,
                                      params=params)

    def list(self, collection, path, retrieve_all=True, **params):
        return self.legacy_client.list(collection, path,
                                       retrieve_all=retrieve_all, **params)

    def show_vim(self, vim, **_params):
        return self.legacy_client.show_vim(vim, **_params)

    def create_vim(self, body):
        return self.legacy_client.create_vim(body)

    def delete_vim(self, vim):
        return self.legacy_client.delete_vim(vim)

    def update_vim(self, vim, body):
        return self.legacy_client.update_vim(vim, body)

    def list_vims(self, retrieve_all=True, **_params):
        return self.legacy_client.list_vims(retrieve_all=retrieve_all,
                                            **_params)

    # VnfPackageClient methods

    def create_vnf_package(self, body):
        return self.vnf_package_client.create_vnf_package(body)

    def list_vnf_packages(self, retrieve_all=True, query_parameter=None,
                          **_params):
        return self.vnf_package_client.list_vnf_packages(
            retrieve_all=retrieve_all, **_params)

    def show_vnf_package(self, vnf_package, **_params):
        return self.vnf_package_client.show_vnf_package(vnf_package, **_params)

    def upload_vnf_package(self, vnf_package, file_data=None, **_params):
        return self.vnf_package_client.upload_vnf_package(
            vnf_package, file_data=file_data, **_params)

    def delete_vnf_package(self, vnf_package):
        return self.vnf_package_client.delete_vnf_package(vnf_package)

    # VnfLCMClient methods.

    def create_vnf_instance(self, body):
        return self.vnf_lcm_client.create_vnf_instance(body)

    def show_vnf_instance(self, vnf_instance, **_params):
        return self.vnf_lcm_client.show_vnf_instance(vnf_instance,
                                                     **_params)

    def list_vnf_instances(self, retrieve_all=True, **_params):
        return self.vnf_lcm_client.list_vnf_instances(
            retrieve_all=retrieve_all, **_params)

    def instantiate_vnf_instance(self, vnf_id, body):
        return self.vnf_lcm_client.instantiate_vnf_instance(vnf_id, body)

    def heal_vnf_instance(self, vnf_id, body):
        return self.vnf_lcm_client.heal_vnf_instance(vnf_id, body)

    def terminate_vnf_instance(self, vnf_id, body):
        return self.vnf_lcm_client.terminate_vnf_instance(vnf_id, body)

    def scale_vnf_instance(self, vnf_id, body):
        return self.vnf_lcm_client.scale_vnf_instance(vnf_id, body)

    def change_ext_conn_vnf_instance(self, vnf_id, body):
        return self.vnf_lcm_client.change_ext_conn_vnf_instance(vnf_id, body)

    def change_vnfpkg_vnf_instance(self, vnf_id, body):
        return self.vnf_lcm_client.change_vnfpkg_vnf_instance(vnf_id, body)

    def delete_vnf_instance(self, vnf_id):
        return self.vnf_lcm_client.delete_vnf_instance(vnf_id)

    def update_vnf_instance(self, vnf_id, body):
        return self.vnf_lcm_client.update_vnf_instance(vnf_id, body)

    def rollback_vnf_instance(self, occ_id):
        return self.vnf_lcm_client.rollback_vnf_instance(occ_id)

    def cancel_vnf_instance(self, occ_id, body):
        return self.vnf_lcm_client.cancel_vnf_instance(occ_id, body)

    def fail_vnf_instance(self, occ_id):
        return self.vnf_lcm_client.fail_vnf_instance(occ_id)

    def retry_vnf_instance(self, occ_id):
        return self.vnf_lcm_client.retry_vnf_instance(occ_id)

    def update_vnf_package(self, vnf_package, body):
        return self.vnf_package_client.update_vnf_package(vnf_package, body)

    def download_vnfd_from_vnf_package(self, vnf_package, accept):
        return self.vnf_package_client.download_vnfd_from_vnf_package(
            vnf_package, accept)

    def download_artifact_from_vnf_package(self, vnf_package, artifact_path):
        return self.vnf_package_client.download_artifact_from_vnf_package(
            vnf_package, artifact_path
        )

    def download_vnf_package(self, vnf_package):
        return self.vnf_package_client.download_vnf_package(vnf_package)

    def list_vnf_lcm_op_occs(self, retrieve_all=True, **_params):
        return self.vnf_lcm_client.list_vnf_lcm_op_occs(
            retrieve_all=retrieve_all, **_params)

    def show_vnf_lcm_op_occs(self, occ_id):
        return self.vnf_lcm_client.show_vnf_lcm_op_occs(occ_id)

    def create_lccn_subscription(self, body):
        return self.vnf_lcm_client.create_lccn_subscription(body)

    def delete_lccn_subscription(self, subsc_id):
        return self.vnf_lcm_client.delete_lccn_subscription(subsc_id)

    def list_lccn_subscriptions(self, retrieve_all=True, **_params):
        return self.vnf_lcm_client.list_lccn_subscriptions(
            retrieve_all=retrieve_all, **_params)

    def show_lccn_subscription(self, subsc_id):
        return self.vnf_lcm_client.show_lccn_subscription(subsc_id)

    def show_vnf_lcm_versions(self, major_version):
        return self.vnf_lcm_client.show_vnf_lcm_versions(major_version)

    # VnfFMClient methods.

    def list_vnf_fm_alarms(self, retrieve_all=True, **_params):
        return self.vnf_fm_client.list_vnf_fm_alarms(
            retrieve_all=retrieve_all, **_params)

    def show_vnf_fm_alarm(self, vnf_fm_alarm_id):
        return self.vnf_fm_client.show_vnf_fm_alarm(vnf_fm_alarm_id)

    def update_vnf_fm_alarm(self, vnf_fm_alarm_id, body):
        return self.vnf_fm_client.update_vnf_fm_alarm(vnf_fm_alarm_id, body)

    def create_vnf_fm_sub(self, body):
        return self.vnf_fm_client.create_vnf_fm_sub(body)

    def list_vnf_fm_subs(self, retrieve_all=True, **_params):
        return self.vnf_fm_client.list_vnf_fm_subs(
            retrieve_all=retrieve_all, **_params)

    def show_vnf_fm_sub(self, vnf_fm_sub_id):
        return self.vnf_fm_client.show_vnf_fm_sub(vnf_fm_sub_id)

    def delete_vnf_fm_sub(self, vnf_fm_sub_id):
        return self.vnf_fm_client.delete_vnf_fm_sub(vnf_fm_sub_id)

    # VnfPMClient methods.

    def create_vnf_pm_job(self, body):
        return self.vnf_pm_client.create_vnf_pm_job(body)

    def list_vnf_pm_jobs(self, retrieve_all=True, **_params):
        return self.vnf_pm_client.list_vnf_pm_jobs(
            retrieve_all=retrieve_all, **_params)

    def show_vnf_pm_job(self, vnf_pm_job_id):
        return self.vnf_pm_client.show_vnf_pm_job(vnf_pm_job_id)

    def update_vnf_pm_job(self, vnf_pm_job_id, body):
        return self.vnf_pm_client.update_vnf_pm_job(vnf_pm_job_id, body)

    def delete_vnf_pm_job(self, vnf_pm_job_id):
        return self.vnf_pm_client.delete_vnf_pm_job(vnf_pm_job_id)

    def show_vnf_pm_report(self, vnf_pm_job_id, vnf_pm_report_id):
        return self.vnf_pm_client.show_vnf_pm_report(
            vnf_pm_job_id, vnf_pm_report_id)

    def create_vnf_pm_threshold(self, body):
        return self.vnf_pm_client.create_vnf_pm_threshold(body)

    def list_vnf_pm_thresholds(self, retrieve_all=True, **_params):
        return self.vnf_pm_client.list_vnf_pm_thresholds(
            retrieve_all=retrieve_all, **_params)

    def show_vnf_pm_threshold(self, vnf_pm_threshold_id):
        return self.vnf_pm_client.show_vnf_pm_threshold(vnf_pm_threshold_id)

    def update_vnf_pm_threshold(self, vnf_pm_threshold_id, body):
        return self.vnf_pm_client.update_vnf_pm_threshold(
            vnf_pm_threshold_id, body)

    def delete_vnf_pm_threshold(self, vnf_pm_threshold_id):
        return self.vnf_pm_client.delete_vnf_pm_threshold(vnf_pm_threshold_id)
