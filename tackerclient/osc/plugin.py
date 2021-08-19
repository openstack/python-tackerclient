#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

"""OpenStackClient plugin for nfv-orchestration service."""

import logging

from osc_lib import utils


LOG = logging.getLogger(__name__)

# Required by the OSC plugin interface
DEFAULT_TACKER_API_VERSION = '1'
API_NAME = 'tackerclient'
API_VERSION_OPTION = 'os_tacker_api_version'
API_VERSIONS = {
    '1': 'tackerclient.v1_0.client.Client',
    '2': 'tackerclient.v1_0.client.Client',
}


def make_client(instance):
    """Returns a client to the ClientManager."""

    api_version = instance._api_version[API_NAME]
    tacker_client = utils.get_client_class(
        API_NAME,
        api_version,
        API_VERSIONS)
    LOG.debug('Instantiating tacker client: %s', tacker_client)

    kwargs = {'service_type': 'nfv-orchestration',
              'region_name': instance._region_name,
              'endpoint_type': instance._interface,
              'interface': instance._interface,
              'session': instance.session,
              'api_version': api_version
              }

    client = tacker_client(**kwargs)

    return client


def build_option_parser(parser):
    """Hook to add global options."""
    parser.add_argument(
        '--os-tacker-api-version',
        metavar='<tacker-api-version>',
        default=utils.env(
            'OS_TACKER_API_VERSION',
            default=DEFAULT_TACKER_API_VERSION))
    return parser
