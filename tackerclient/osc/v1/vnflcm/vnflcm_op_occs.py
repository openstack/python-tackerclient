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
from tackerclient.i18n import _


class RollbackVnfLcmOp(command.Command):
    def get_parser(self, prog_name):
        """Add arguments to parser.

        Args:
            prog_name ([type]): program name

        Returns:
            parser([ArgumentParser]):
        """
        parser = super(RollbackVnfLcmOp, self).get_parser(prog_name)
        parser.add_argument(
            'vnf_lcm_op_occ_id',
            metavar="<vnf-lcm-op-occ-id>",
            help=_('VNF lifecycle management operation occurrence ID.'))

        return parser

    def take_action(self, parsed_args):
        """Execute rollback_vnf_instance and output comment.

        Args:
            parsed_args ([Namespace]): arguments of CLI.
        """
        client = self.app.client_manager.tackerclient
        result = client.rollback_vnf_instance(parsed_args.vnf_lcm_op_occ_id)
        if not result:
            print((_('Rollback request for LCM operation %(id)s has been'
                     ' accepted') % {'id': parsed_args.vnf_lcm_op_occ_id}))
