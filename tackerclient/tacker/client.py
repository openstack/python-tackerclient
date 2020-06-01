# Copyright 2012 OpenStack Foundation.
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

from tackerclient.common._i18n import _
from tackerclient.common import exceptions
from tackerclient.common import utils


API_NAME = 'nfv-orchestration'
API_VERSIONS = {
    '1.0': 'tackerclient.v1_0.client.Client',
}


def make_client(instance):
    """Returns an tacker client."""

    tacker_client = utils.get_client_class(
        API_NAME,
        instance._api_version[API_NAME],
        API_VERSIONS,
    )
    instance.initialize()
    url = instance._url
    url = url.rstrip("/")
    if '1.0' == instance._api_version[API_NAME]:
        client = tacker_client(username=instance._username,
                               tenant_name=instance._tenant_name,
                               password=instance._password,
                               region_name=instance._region_name,
                               auth_url=instance._auth_url,
                               endpoint_url=url,
                               endpoint_type=instance._endpoint_type,
                               token=instance._token,
                               auth_strategy=instance._auth_strategy,
                               insecure=instance._insecure,
                               ca_cert=instance._ca_cert,
                               retries=instance._retries,
                               raise_errors=instance._raise_errors,
                               session=instance._session,
                               auth=instance._auth)
        return client
    else:
        raise exceptions.UnsupportedVersion(
            reason=_("API version %s is not supported") %
            instance._api_version[API_NAME])


def Client(api_version, *args, **kwargs):
    """Return an tacker client.

    :param api_version: only 1.0 is supported now
    """
    tacker_client = utils.get_client_class(
        API_NAME,
        api_version,
        API_VERSIONS,
    )
    return tacker_client(*args, **kwargs)
