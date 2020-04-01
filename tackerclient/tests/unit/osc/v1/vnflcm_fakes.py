# Copyright (C) 2020 NTT DATA
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

from oslo_utils.fixture import uuidsentinel


def vnf_instance_response(attrs=None):
    """Create a fake vnf instance.

    :param Dictionary attrs:
        A dictionary with all attributes
    :return:
        A vnf instance dict
    """
    attrs = attrs or {}

    # Set default attributes.
    dummy_vnf_instance = {
        "id": uuidsentinel.vnf_instance_id,
        "vnfInstanceName": "Fake-VNF-Instance",
        "vnfInstanceDescription": "Fake VNF",
        "vnfdId": uuidsentinel.vnf_package_vnfd_id,
        "vnfProvider": "NTT NS lab",
        "vnfProductName": "Sample VNF",
        "vnfSoftwareVersion": "1.0",
        "vnfdVersion": "1.0",
        "instantiationState": "NOT_INSTANTIATED",
        "links": "vnflcm/v1/vnf_instances/" + uuidsentinel.vnf_instance_id +
                 "/instantiate"
    }
    return dummy_vnf_instance


def get_vnflcm_data(vnf_instance):
    """Get the vnf instance data.

    :return:
        A tuple object sorted based on the name of the columns.
    """
    # return the list of data as per column order
    return tuple([vnf_instance[key] for key in sorted(vnf_instance.keys())])
