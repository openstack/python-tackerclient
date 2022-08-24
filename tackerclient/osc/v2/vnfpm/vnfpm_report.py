# Copyright (C) 2022 Fujitsu
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

import logging

from osc_lib.command import command
from osc_lib import utils

from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils

LOG = logging.getLogger(__name__)

_FORMATTERS = {
    'entries': tacker_osc_utils.FormatComplexDataColumn
}

_VNF_PM_JOB_ID = 'vnf_pm_job_id'
_VNF_PM_REPORT_ID = 'vnf_pm_report_id'


def _get_columns(vnfpm_report_obj):
    column_map = {
        'entries': 'Entries'
    }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(
        vnfpm_report_obj, column_map)


class ShowVnfPmReport(command.ShowOne):
    _description = _("Display VNF PM report details")

    def get_parser(self, prog_name):
        parser = super(ShowVnfPmReport, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_PM_JOB_ID,
            metavar="<vnf-pm-job-id>",
            help=_("VNF PM job id where the VNF PM report is located"))
        parser.add_argument(
            _VNF_PM_REPORT_ID,
            metavar="<vnf-pm-report-id>",
            help=_("VNF PM report ID to display"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj = client.show_vnf_pm_report(
            parsed_args.vnf_pm_job_id, parsed_args.vnf_pm_report_id)
        display_columns, columns = _get_columns(obj)
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj),
            columns, formatters=_FORMATTERS,
            mixed_case_fields=None)
        return (display_columns, data)
