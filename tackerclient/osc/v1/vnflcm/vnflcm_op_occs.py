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
from osc_lib import utils
from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils

_VNF_LCM_OP_OCC_ID = 'vnf_lcm_op_occ_id'

_MIXED_CASE_FIELDS = ['operationState', 'stateEnteredTime', 'startTime',
                      'vnfInstanceId', 'grantId', 'isAutomaticInvocation',
                      'isCancelPending', 'cancelMode', 'operationParams',
                      'resourceChanges', 'changedInfo',
                      'changedExtConnectivity']

_FORMATTERS = {
    'operationParams': tacker_osc_utils.FormatComplexDataColumn,
    'error': tacker_osc_utils.FormatComplexDataColumn,
    'resourceChanges': tacker_osc_utils.FormatComplexDataColumn,
    'changedInfo': tacker_osc_utils.FormatComplexDataColumn,
    'changedExtConnectivity': tacker_osc_utils.FormatComplexDataColumn,
    '_links': tacker_osc_utils.FormatComplexDataColumn
}

_ATTR_MAP = (
    ('id', 'id', tacker_osc_utils.LIST_BOTH),
    ('operationState', 'operationState', tacker_osc_utils.LIST_BOTH),
    ('vnfInstanceId', 'vnfInstanceId', tacker_osc_utils.LIST_BOTH),
    ('operation', 'operation', tacker_osc_utils.LIST_BOTH)
)


def _get_columns(vnflcm_op_occ_obj, action=None):

    column_map = {
        'id': 'ID',
        'operationState': 'Operation State',
        'stateEnteredTime': 'State Entered Time',
        'startTime': 'Start Time',
        'vnfInstanceId': 'VNF Instance ID',
        'operation': 'Operation',
        'isAutomaticInvocation': 'Is Automatic Invocation',
        'isCancelPending': 'Is Cancel Pending',
        'error': 'Error',
        '_links': 'Links'
    }

    if action == 'show':
        column_map.update(
            {'operationParams': 'Operation Parameters',
             'grantId': 'Grant ID',
             'resourceChanges': 'Resource Changes',
             'changedInfo': 'Changed Info',
             'cancelMode': 'Cancel Mode',
             'changedExtConnectivity': 'Changed External Connectivity'}
        )

    return sdk_utils.get_osc_show_columns_for_sdk_resource(vnflcm_op_occ_obj,
                                                           column_map)


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
            _VNF_LCM_OP_OCC_ID,
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


class CancelVnfLcmOp(command.ShowOne):
    _description = _("Cancel VNF Instance")

    def get_parser(self, prog_name):
        """Add arguments to parser.

        Args:
            prog_name ([type]): program name

        Returns:
            parser([ArgumentParser]):
        """
        parser = super(CancelVnfLcmOp, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_LCM_OP_OCC_ID,
            metavar="<vnf-lcm-op-occ-id>",
            help=_('VNF lifecycle management operation occurrence ID.'))
        parser.add_argument(
            "--cancel-mode",
            default='GRACEFUL',
            metavar="<cancel-mode>",
            choices=['GRACEFUL', 'FORCEFUL'],
            help=_("Cancel mode can be 'GRACEFUL' or 'FORCEFUL'. "
                   "Default is 'GRACEFUL'"))
        return parser

    def take_action(self, parsed_args):
        """Execute cancel_vnf_instance and output comment.

        Args:
            parsed_args ([Namespace]): arguments of CLI.
        """
        client = self.app.client_manager.tackerclient
        result = client.cancel_vnf_instance(
            parsed_args.vnf_lcm_op_occ_id,
            {'cancelMode': parsed_args.cancel_mode})
        if not result:
            print((_('Cancel request for LCM operation %(id)s has been'
                     ' accepted') % {'id': parsed_args.vnf_lcm_op_occ_id}))


class FailVnfLcmOp(command.ShowOne):
    _description = _("Fail VNF Instance")

    def get_parser(self, prog_name):
        """Add arguments to parser.

        Args:
            prog_name ([type]): program name

        Returns:
            parser([ArgumentParser]):
        """
        parser = super(FailVnfLcmOp, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_LCM_OP_OCC_ID,
            metavar="<vnf-lcm-op-occ-id>",
            help=_('VNF lifecycle management operation occurrence ID.'))
        return parser

    def take_action(self, parsed_args):
        """Execute fail_vnf_instance and output response.

        Args:
            parsed_args ([Namespace]): arguments of CLI.
        """
        client = self.app.client_manager.tackerclient
        obj = client.fail_vnf_instance(parsed_args.vnf_lcm_op_occ_id)
        display_columns, columns = _get_columns(obj)
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj),
            columns, formatters=_FORMATTERS,
            mixed_case_fields=_MIXED_CASE_FIELDS)
        return (display_columns, data)


class RetryVnfLcmOp(command.Command):
    _description = _("Retry VNF Instance")

    def get_parser(self, prog_name):
        """Add arguments to parser.

        Args:
            prog_name ([type]): program name

        Returns:
            parser([ArgumentParser]):
        """

        parser = super(RetryVnfLcmOp, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_LCM_OP_OCC_ID,
            metavar="<vnf-lcm-op-occ-id>",
            help=_('VNF lifecycle management operation occurrence ID.'))
        return parser

    def take_action(self, parsed_args):
        """Execute retry_vnf_instance and output comment.

        Args:
            parsed_args ([Namespace]): arguments of CLI.
        """
        client = self.app.client_manager.tackerclient
        result = client.retry_vnf_instance(parsed_args.vnf_lcm_op_occ_id)
        if not result:
            print((_('Retry request for LCM operation %(id)s has been'
                     ' accepted') % {'id': parsed_args.vnf_lcm_op_occ_id}))


class ListVnfLcmOp(command.Lister):
    _description = _("List LCM Operation Occurrences")

    def get_parser(self, program_name):
        """Add arguments to parser.

        Args:
            program_name ([type]): program name

        Returns:
            parser([ArgumentParser]):
        """
        parser = super(ListVnfLcmOp, self).get_parser(program_name)
        parser.add_argument(
            "--filter",
            metavar="<filter>",
            help=_("Attribute-based-filtering parameters"),
        )
        fields_exclusive_group = parser.add_mutually_exclusive_group(
            required=False)
        fields_exclusive_group.add_argument(
            "--fields",
            metavar="<fields>",
            help=_("Complex attributes to be included into the response"),
        )
        fields_exclusive_group.add_argument(
            "--exclude-fields",
            metavar="<exclude-fields>",
            help=_("Complex attributes to be excluded from the response"),
        )
        return parser

    def get_attributes(self, exclude=None):
        """Get attributes.

        Args:
            exclude([exclude]): a list of fields which needs to exclude.

        Returns:
            attributes([attributes]): a list of table entry definitions.
            Each entry should be a tuple consisting of
            (API attribute name, header name, listing mode).
        """
        fields = [
            {
                "key": "id",
                "value": "ID"
            },
            {
                "key": "operationState",
                "value": "Operation State"
            },
            {
                "key": "vnfInstanceId",
                "value": "VNF Instance ID"
            },
            {
                "key": "operation",
                "value": "Operation"
            }
        ]

        attributes = []
        if exclude is None:
            exclude = []

        for field in fields:
            if field['value'] not in exclude:
                attributes.extend([(field['key'], field['value'],
                                  tacker_osc_utils.LIST_BOTH)])
        return tuple(attributes)

    def take_action(self, parsed_args):
        """Execute list_vnflcm_op_occs and output response.

        Args:
            parsed_args ([Namespace]): arguments of CLI.
        """
        params = {}
        exclude_fields = []
        extra_fields = []

        if parsed_args.filter:
            params['filter'] = parsed_args.filter
        if parsed_args.fields:
            params['fields'] = parsed_args.fields
            fields = parsed_args.fields.split(',')
            for field in fields:
                extra_fields.append(field.split('/')[0])
        if parsed_args.exclude_fields:
            params['exclude-fields'] = parsed_args.exclude_fields
            fields = parsed_args.exclude_fields.split(',')
            exclude_fields.extend(fields)

        client = self.app.client_manager.tackerclient
        vnflcm_op_occs = client.list_vnf_lcm_op_occs(**params)
        headers, columns = tacker_osc_utils.get_column_definitions(
            self.get_attributes(exclude=exclude_fields),
            long_listing=True)

        dictionary_properties = (utils.get_dict_properties(
            s, columns, mixed_case_fields=_MIXED_CASE_FIELDS)
            for s in vnflcm_op_occs
        )

        return (headers, dictionary_properties)


class ShowVnfLcmOp(command.ShowOne):
    _description = _("Display Operation Occurrence details")

    def get_parser(self, program_name):
        """Add arguments to parser.

        Args:
            program_name ([type]): program name

        Returns:
            parser([ArgumentParser]):
        """
        parser = super(ShowVnfLcmOp, self).get_parser(program_name)
        parser.add_argument(
            _VNF_LCM_OP_OCC_ID,
            metavar="<vnf-lcm-op-occ-id>",
            help=_('VNF lifecycle management operation occurrence ID.'))
        return parser

    def take_action(self, parsed_args):
        """Execute show_vnf_lcm_op_occs and output response.

        Args:
            parsed_args ([Namespace]): arguments of CLI.
        """
        client = self.app.client_manager.tackerclient
        obj = client.show_vnf_lcm_op_occs(parsed_args.vnf_lcm_op_occ_id)
        display_columns, columns = _get_columns(obj, action='show')
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj),
            columns, formatters=_FORMATTERS,
            mixed_case_fields=_MIXED_CASE_FIELDS)
        return (display_columns, data)
