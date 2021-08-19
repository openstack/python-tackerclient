# Copyright (C) 2021 Nippon Telegraph and Telephone Corporation
# All Rights Reserved.
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

from osc_lib.command import command

from tackerclient.common import exceptions
from tackerclient.i18n import _


SUPPORTED_VERSIONS = [1, 2]


class VnfLcmVersions(command.ShowOne):
    _description = _("Show VnfLcm Api versions")

    def get_parser(self, prog_name):
        parser = super(VnfLcmVersions, self).get_parser(prog_name)
        parser.add_argument(
            '--major-version',
            metavar="<major-version>",
            type=int,
            help=_('Show only specify major version.'))
        return parser

    def take_action(self, parsed_args):
        v = None
        if parsed_args.major_version:
            if parsed_args.major_version not in SUPPORTED_VERSIONS:
                msg = _("Major version %d is not supported")
                reason = msg % parsed_args.major_version
                raise exceptions.InvalidInput(reason=reason)
            v = "v{}".format(parsed_args.major_version)

        client = self.app.client_manager.tackerclient
        data = client.show_vnf_lcm_versions(v)

        return (tuple(data.keys()), tuple(data.values()))
