# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_utils.fixture import uuidsentinel
from oslo_utils import uuidutils

from tackerclient.osc import utils as tacker_osc_utils


def vnflcm_op_occ_response(attrs=None, action=''):
    """Create a fake vnflcm op occurrence.

    :param Dictionary attrs:
        A dictionary with all attributes
    :return:
        A vnf lcm op occs dict
    """
    attrs = attrs or {}

    # Set default attributes.
    dummy_vnf_lcm_op_occ = {
        "id": uuidsentinel.vnflcm_op_occ_id,
        "operationState": "STARTING",
        "stateEnteredTime": "2018-12-22T16:59:45.187Z",
        "startTime": "2018-12-22T16:59:45.187Z",
        "vnfInstanceId": "376f37f3-d4e9-4d41-8e6a-9b0ec98695cc",
        "grantId": "",
        "operation": "INSTANTIATE",
        "isAutomaticInvocation": "true",
        "operationParams": {
            "flavourId": "default",
            "instantiationLevelId": "n-mme-min"
        },
        "isCancelPending": "true",
        "cancelMode": "",
        "error": {
            "status": "500",
            "detail": "internal server error"
        },
        "resourceChanges": [],
        "changedInfo": [],
        "changedExtConnectivity": [],
        "_links": {
            "self": ""
        }
    }

    if action == 'fail':
        fail_not_needed_columns = [
            'grantId', 'operationParams',
            'cancelMode', 'resourceChanges', 'changedInfo',
            'changedExtConnectivity']

        for key in fail_not_needed_columns:
            del dummy_vnf_lcm_op_occ[key]

    # Overwrite default attributes.
    dummy_vnf_lcm_op_occ.update(attrs)

    return dummy_vnf_lcm_op_occ


def get_vnflcm_op_occ_data(vnf_lcm_op_occ, columns=None):
    """Get the vnflcm op occurrence.

    :return:
        A tuple object sorted based on the name of the columns.
    """
    complex_attributes = [
        'operationParams', 'error', 'resourceChanges',
        'changedInfo', 'changedExtConnectivity', 'links']

    for attribute in complex_attributes:
        if vnf_lcm_op_occ.get(attribute):
            vnf_lcm_op_occ.update(
                {attribute: tacker_osc_utils.FormatComplexDataColumn(
                    vnf_lcm_op_occ[attribute])})

    # return the list of data as per column order
    if columns:
        return tuple([vnf_lcm_op_occ[key] for key in columns])

    return tuple([vnf_lcm_op_occ[key] for key in sorted(
        vnf_lcm_op_occ.keys())])


def create_vnflcm_op_occs(count=2):
    """Create multiple fake vnflcm op occs.

    :param count: The number of vnflcm op occs to fake
    :return:
        A list of fake vnflcm op occs dictionary
    """
    vnflcm_op_occs = []
    for i in range(0, count):
        unique_id = uuidutils.generate_uuid()
        vnflcm_op_occs.append(vnflcm_op_occ_response(attrs={'id': unique_id}))
    return vnflcm_op_occs
