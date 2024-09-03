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
from oslo_utils import uuidutils

from tackerclient.osc import utils as tacker_osc_utils


def vnf_instance_response(attrs=None, instantiation_state='NOT_INSTANTIATED'):
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
        "vnfPkgId": uuidsentinel.uuid,
        "_links": "vnflcm/v1/vnf_instances/" + uuidsentinel.vnf_instance_id +
                  "/instantiate",
        "instantiationState": instantiation_state,
        "vnfConfigurableProperties": {
            "test": "test_value"}}
    if instantiation_state == 'INSTANTIATED':
        dummy_vnf_instance.update({
            "vimConnectionInfo": [{
                'id': uuidsentinel.uuid,
                'vimId': uuidsentinel.vimId,
                'vimType': 'openstack',
                'interfaceInfo': {'k': 'v'},
                'accessInfo': {'k': 'v'},
                'extra': {'k': 'v'}
            }],
            "instantiatedVnfInfo": {
                "flavourId": uuidsentinel.flavourId,
                "vnfState": "STARTED",
                "extCpInfo": [{
                    'id': uuidsentinel.extCpInfo_uuid,
                    'cpdId': uuidsentinel.cpdId_uuid,
                    'cpProtocolInfo': [{
                        'layerProtocol': 'IP_OVER_ETHERNET',
                        'ipOverEthernet': '{}'
                    }],
                    'extLinkPortId': uuidsentinel.extLinkPortId_uuid,
                    'metadata': {'k': 'v'},
                    'associatedVnfcCpId': uuidsentinel.associatedVnfcCpId_uuid
                }],
                "extVirtualLinkInfo": [{
                    'id': uuidsentinel.extVirtualLinkInfo_uuid,
                    'resourceHandle': {},
                    'extLinkPorts': []
                }],
                "extManagedVirtualLinkInfo": [{
                    "id": uuidsentinel.extManagedVirtualLinkInfo_uuid,
                    'vnfVirtualLinkDescId': {},
                    'networkResource': {},
                    'vnfLinkPorts': []
                }],
                "vnfcResourceInfo": [{
                    'id': uuidsentinel.vnfcResourceInfo_uuid,
                    'vduId': uuidsentinel.vduId_uuid,
                    'computeResource': {},
                    'storageResourceIds': [],
                    'reservationId': uuidsentinel.reservationId,
                }],
                "vnfVirtualLinkResourceInfo": [{
                    'id': uuidsentinel.vnfVirtualLinkResourceInfo,
                    'vnfVirtualLinkDescId': 'VL4',
                    'networkResource': {},
                    'reservationId': uuidsentinel.reservationId,
                    'vnfLinkPorts': [],
                    'metadata': {'k': 'v'}
                }],
                "virtualStorageResourceInfo": [{
                    'id': uuidsentinel.virtualStorageResourceInfo,
                    'virtualStorageDescId': uuidsentinel.virtualStorageDescId,
                    'storageResource': {},
                    'reservationId': uuidsentinel.reservationId,
                    'metadata': {'k': 'v'}
                }]
            },
            "_links": {
                'self': 'self_link',
                'indicators': None,
                'instantiate': 'instantiate_link'
            }
        })

    # Overwrite default attributes.
    dummy_vnf_instance.update(attrs)

    return dummy_vnf_instance


def get_vnflcm_data(vnf_instance, list_action=False, columns=None):
    """Get the vnf instance data.

    :return:
        A tuple object sorted based on the name of the columns.
    """
    vnf = vnf_instance.copy()
    complex_attributes = ['vimConnectionInfo', 'instantiatedVnfInfo', '_links']
    for attribute in complex_attributes:
        if vnf.get(attribute):
            vnf.update(
                {attribute: tacker_osc_utils.FormatComplexDataColumn(
                    vnf[attribute])})

    if list_action:
        for item in ['vnfInstanceDescription', 'vnfdVersion']:
            vnf.pop(item)

    # return the list of data as per column order
    if columns:
        return tuple([vnf[key] for key in columns])

    return tuple([vnf[key] for key in sorted(
        vnf.keys())])


def create_vnf_instances(count=2):
    """Create multiple fake vnf instances.

    :param count: The number of vnf instances to fake
    :return:
        A list of fake vnf instances dictionary
    """
    vnf_instances = []
    for i in range(0, count):
        unique_id = uuidutils.generate_uuid()
        vnf_instances.append(vnf_instance_response(attrs={'id': unique_id}))
    return vnf_instances
