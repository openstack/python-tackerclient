# Copyright (C) 2023 Fujitsu
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

from oslo_utils import uuidutils

from tackerclient.osc import utils as tacker_osc_utils


def create_vnf_pm_thresholds(count=2):
    """Create multiple fake vnf pm thresholds.

    :param int count:
        The number of vnf_pm_thresholds to fake
    :return:
        A list of fake vnf pm thresholds dictionary
    """
    vnf_pm_thresholds = []
    for _ in range(0, count):
        unique_id = uuidutils.generate_uuid()
        vnf_pm_thresholds.append(vnf_pm_threshold_response(
            attrs={'id': unique_id}))
    return vnf_pm_thresholds


def vnf_pm_threshold_response(attrs=None, action=None):
    """Create a fake vnf pm threshold.

    :param Dictionary attrs:
        A dictionary with all attributes
    :param String action:
        The operation performed on threshold
    :return:
        A pm threshold dict
    """
    if action == 'update':
        fake_vnf_pm_threshold = {
            "callbackUri": "/nfvo/notify/threshold",
        }
        return fake_vnf_pm_threshold

    attrs = attrs or {}
    # Set default attributes.
    fake_vnf_pm_threshold = {
        "id": "2bb72d78-b1d9-48fe-8c64-332654ffeb5d",
        "objectType": "Vnfc",
        "objectInstanceId": "object-instance-id-1",
        "subObjectInstanceIds": [
            "sub-object-instance-id-2"
        ],
        "criteria": {
            "performanceMetric": "VCpuUsageMeanVnf.object-instance-id-1",
            "thresholdType": "SIMPLE",
            "simpleThresholdDetails": {
                "thresholdValue": 500.5,
                "hysteresis": 10.5
            }
        },
        "callbackUri": "/nfvo/notify/threshold",
        "_links": {
            "self": {
                "href": "/vnfpm/v2/thresholds/"
                        "78a39661-60a8-4824-b989-88c1b0c3534a"
            },
            "object": {
                "href": "/vnflcm/v1/vnf_instances/"
                        "0e5f3086-4e79-47ed-a694-54c29155fa26"
            }
        }
    }

    # Overwrite default attributes.
    fake_vnf_pm_threshold.update(attrs)

    return fake_vnf_pm_threshold


def get_vnfpm_threshold_data(vnf_pm_threshold, columns=None):
    """Get the vnfpm threshold.

    :param Dictionary vnf_pm_threshold:
        A dictionary with vnf_pm_threshold
    :param List columns:
        A list of column names
    :return:
        A tuple object sorted based on the name of the columns.
    """
    complex_attributes = ['subObjectInstanceIds',
                          'criteria', '_links', 'authentication']

    for attribute in complex_attributes:
        if vnf_pm_threshold.get(attribute):
            vnf_pm_threshold.update(
                {attribute: tacker_osc_utils.FormatComplexDataColumn(
                    vnf_pm_threshold[attribute])})

    # return the list of data as per column order
    if columns is None:
        columns = sorted(vnf_pm_threshold.keys())
    return tuple([vnf_pm_threshold[key] for key in columns])
