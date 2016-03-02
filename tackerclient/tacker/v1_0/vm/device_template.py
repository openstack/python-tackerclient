#
# Copyright 2013 Intel
# Copyright 2013 Isaku Yamahata <isaku.yamahata at intel com>
#                               <isaku.yamahata at gmail com>
# All Rights Reserved.
#
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
# @author: Isaku Yamahata, Intel

from tackerclient.common.utils import deprecated
from tackerclient.tacker import v1_0 as tackerV10


_DEVICE_TEMPLATE = "device_template"


@deprecated('device-template-list')
class ListDeviceTemplate(tackerV10.ListCommand):
    """List device template that belong to a given tenant."""

    resource = _DEVICE_TEMPLATE


@deprecated('device-template-show')
class ShowDeviceTemplate(tackerV10.ShowCommand):
    """show information of a given DeviceTemplate."""

    resource = _DEVICE_TEMPLATE


@deprecated('device-template-create')
class CreateDeviceTemplate(tackerV10.CreateCommand):
    """create a DeviceTemplate."""

    resource = _DEVICE_TEMPLATE

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name',
            help='Set a name for the devicetemplate')
        parser.add_argument(
            '--description',
            help='Set a description for the devicetemplate')
        parser.add_argument(
            '--template-service-type',
            action='append',
            help='Add a servicetype for the devicetemplate')
        parser.add_argument(
            '--infra-driver',
            help='Set a infra driver name for the devicetemplate')
        parser.add_argument(
            '--mgmt-driver',
            help='Set a manegement driver name for the devicetemplate')
        parser.add_argument(
            '--attribute',
            nargs=2,
            action='append',
            help='Set a servicetypes for the devicetemplate')

    def args2body(self, parsed_args):
        body = {
            self.resource: {
                'service_types': [
                    {'service_type': service_type}
                    for service_type in parsed_args.template_service_type],
                'infra_driver': parsed_args.infra_driver,
                'mgmt_driver': parsed_args.mgmt_driver,
            }
        }
        if parsed_args.attribute:
            body[self.resource]['attributes'] = dict(parsed_args.attribute)
        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description'])
        return body


@deprecated('device-template-update')
class UpdateDeviceTemplate(tackerV10.UpdateCommand):
    """Update a given DeviceTemplate."""

    resource = _DEVICE_TEMPLATE
    allow_names = False


@deprecated('device-template-delete')
class DeleteDeviceTemplate(tackerV10.DeleteCommand):
    """Delete a given DeviceTemplate."""
    resource = _DEVICE_TEMPLATE
