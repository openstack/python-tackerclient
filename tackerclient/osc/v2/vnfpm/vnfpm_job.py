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

from functools import reduce
from osc_lib.command import command
from osc_lib import utils

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils

LOG = logging.getLogger(__name__)

_FORMATTERS = {
    'objectInstanceIds': tacker_osc_utils.FormatComplexDataColumn,
    'subObjectInstanceIds': tacker_osc_utils.FormatComplexDataColumn,
    'criteria': tacker_osc_utils.FormatComplexDataColumn,
    'reports': tacker_osc_utils.FormatComplexDataColumn,
    '_links': tacker_osc_utils.FormatComplexDataColumn
}

_MIXED_CASE_FIELDS = (
    'objectType', 'objectInstanceIds', 'subObjectInstanceIds', 'callbackUri'
)

_MIXED_CASE_FIELDS_UPDATE = (
    'callbackUri'
)

_VNF_PM_JOB_ID = 'vnf_pm_job_id'


def _get_columns(vnfpm_job_obj, action=None):
    if action == 'update':
        column_map = {
            'callbackUri': 'Callback Uri'
        }
    else:
        column_map = {
            'id': 'ID',
            'objectType': 'Object Type',
            'objectInstanceIds': 'Object Instance Ids',
            'subObjectInstanceIds': 'Sub Object Instance Ids',
            'criteria': 'Criteria',
            'callbackUri': 'Callback Uri',
            'reports': 'Reports',
            '_links': 'Links'
        }

    if action == 'show':
        column_map.update(
            {'reports': 'Reports'}
        )

    return sdk_utils.get_osc_show_columns_for_sdk_resource(
        vnfpm_job_obj, column_map)


class CreateVnfPmJob(command.ShowOne):
    _description = _("Create a new VNF PM job")

    def get_parser(self, prog_name):
        parser = super(CreateVnfPmJob, self).get_parser(prog_name)
        parser.add_argument(
            'request_file',
            metavar="<param-file>",
            help=_('Specify create VNF PM job request '
                   'parameters in a json file.'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnf_pm_job = client.create_vnf_pm_job(
            tacker_osc_utils.jsonfile2body(parsed_args.request_file))
        display_columns, columns = _get_columns(vnf_pm_job)
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnf_pm_job), columns,
            formatters=_FORMATTERS, mixed_case_fields=_MIXED_CASE_FIELDS)
        return (display_columns, data)


class ListVnfPmJob(command.Lister):
    _description = _("List VNF PM jobs")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(ListVnfPmJob, self).get_parser(prog_name)
        parser.add_argument(
            "--filter",
            metavar="<filter>",
            help=_("Attribute-based-filtering parameters"),
        )
        fields_exclusive_group = parser.add_mutually_exclusive_group(
            required=False)
        fields_exclusive_group.add_argument(
            "--all_fields",
            action="store_true",
            default=False,
            help=_("Include all complex attributes in the response"),
        )
        fields_exclusive_group.add_argument(
            "--fields",
            metavar="fields",
            help=_("Complex attributes to be included into the response"),
        )
        fields_exclusive_group.add_argument(
            "--exclude_fields",
            metavar="exclude-fields",
            help=_("Complex attributes to be excluded from the response"),
        )
        parser.add_argument(
            "--exclude_default",
            action="store_true",
            default=False,
            help=_("Indicates to exclude all complex attributes"
                   " from the response. This argument can be used alone or"
                   " with --fields and --filter. For all other combinations"
                   " tacker server will throw bad request error"),
        )
        return parser

    def case_modify(self, field):
        return reduce(
            lambda x, y: x + (' ' if y.isupper() else '') + y, field).title()

    def get_attributes(self, extra_fields=None, all_fields=False,
                       exclude_fields=None, exclude_default=False):
        fields = ['id', 'objectType', '_links']
        complex_fields = [
            'objectInstanceIds',
            'subObjectInstanceIds',
            'criteria',
            'reports']
        simple_fields = ['callbackUri']

        if extra_fields:
            fields.extend(extra_fields)

        if exclude_fields:
            fields.extend([field for field in complex_fields
                           if field not in exclude_fields])
        if all_fields:
            fields.extend(complex_fields)
            fields.extend(simple_fields)

        if exclude_default:
            fields.extend(simple_fields)

        attrs = []
        for field in fields:
            if field == '_links':
                attrs.extend([(field, 'Links', tacker_osc_utils.LIST_BOTH)])
            else:
                attrs.extend([(field, self.case_modify(field),
                               tacker_osc_utils.LIST_BOTH)])

        return tuple(attrs)

    def take_action(self, parsed_args):
        _params = {}
        extra_fields = []
        exclude_fields = []
        all_fields = False
        exclude_default = False
        if parsed_args.filter:
            _params['filter'] = parsed_args.filter
        if parsed_args.fields:
            _params['fields'] = parsed_args.fields
            fields = parsed_args.fields.split(',')
            for field in fields:
                extra_fields.append(field.split('/')[0])
        if parsed_args.exclude_fields:
            _params['exclude_fields'] = parsed_args.exclude_fields
            fields = parsed_args.exclude_fields.split(',')
            exclude_fields.extend(fields)
        if parsed_args.exclude_default:
            _params['exclude_default'] = None
            exclude_default = True
        if parsed_args.all_fields:
            _params['all_fields'] = None
            all_fields = True

        client = self.app.client_manager.tackerclient
        data = client.list_vnf_pm_jobs(**_params)
        headers, columns = tacker_osc_utils.get_column_definitions(
            self.get_attributes(extra_fields, all_fields, exclude_fields,
                                exclude_default), long_listing=True)
        return (headers,
                (utils.get_dict_properties(
                    s, columns, formatters=_FORMATTERS,
                    mixed_case_fields=_MIXED_CASE_FIELDS,
                ) for s in data['vnf_pm_jobs']))


class ShowVnfPmJob(command.ShowOne):
    _description = _("Display VNF PM job details")

    def get_parser(self, prog_name):
        parser = super(ShowVnfPmJob, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_PM_JOB_ID,
            metavar="<vnf-pm-job-id>",
            help=_("VNF PM job ID to display"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj = client.show_vnf_pm_job(parsed_args.vnf_pm_job_id)
        display_columns, columns = _get_columns(obj, action='show')
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj), columns,
            mixed_case_fields=_MIXED_CASE_FIELDS,
            formatters=_FORMATTERS)
        return (display_columns, data)


class UpdateVnfPmJob(command.ShowOne):
    _description = _("Update information about an individual VNF PM job")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(UpdateVnfPmJob, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_PM_JOB_ID,
            metavar="<vnf-pm-job-id>",
            help=_("VNF PM job ID to update.")
        )
        parser.add_argument(
            'request_file',
            metavar="<param-file>",
            help=_('Specify update PM job request '
                   'parameters in a json file.'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        updated_values = client.update_vnf_pm_job(
            parsed_args.vnf_pm_job_id,
            tacker_osc_utils.jsonfile2body(parsed_args.request_file))
        display_columns, columns = _get_columns(updated_values, 'update')
        data = utils.get_item_properties(
            sdk_utils.DictModel(updated_values), columns,
            mixed_case_fields=_MIXED_CASE_FIELDS_UPDATE)
        return (display_columns, data)


class DeleteVnfPmJob(command.Command):
    _description = _("Delete VNF PM job")

    def get_parser(self, prog_name):
        parser = super(DeleteVnfPmJob, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_PM_JOB_ID,
            metavar="<vnf-pm-job-id>",
            nargs="+",
            help=_("VNF PM job ID(s) to delete"))
        return parser

    def take_action(self, parsed_args):
        error_count = 0
        client = self.app.client_manager.tackerclient
        vnf_pm_job_ids = parsed_args.vnf_pm_job_id

        for job_id in vnf_pm_job_ids:
            try:
                client.delete_vnf_pm_job(job_id)
            except Exception as e:
                error_count += 1
                LOG.error(_("Failed to delete VNF PM job with "
                            "ID '%(job_id)s': %(e)s"),
                          {'job_id': job_id, 'e': e})

        total = len(vnf_pm_job_ids)
        if error_count > 0:
            msg = (_("Failed to delete %(error_count)s of %(total)s "
                     "VNF PM jobs.") % {'error_count': error_count,
                                        'total': total})
            raise exceptions.CommandError(message=msg)

        if total > 1:
            print(_('All specified VNF PM jobs are deleted '
                    'successfully'))
        else:
            print(_("VNF PM job '%s' deleted "
                    "successfully") % vnf_pm_job_ids[0])
