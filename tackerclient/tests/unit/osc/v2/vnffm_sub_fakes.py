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

from oslo_utils import uuidutils

from tackerclient.osc import utils as tacker_osc_utils


def create_vnf_fm_subs(count=2):
    """Create multiple fake vnf packages.

    :param int count:
        The number of vnf_fm_subs to fake
    :return:
        A list of fake vnf fm subs dictionary
    """
    vnf_fm_subs = []
    for i in range(0, count):
        unique_id = uuidutils.generate_uuid()
        vnf_fm_subs.append(vnf_fm_sub_response(attrs={'id': unique_id}))
    return vnf_fm_subs


def vnf_fm_sub_response(attrs=None):
    """Create a fake vnf fm sub.

    :param Dictionary attrs:
        A dictionary with all attributes
    :return:
        A FakeVnfFmAlarm dict
    """

    attrs = attrs or {}
    # Set default attributes.
    fake_vnf_fm_sub = {
        "id": "78a39661-60a8-4824-b989-88c1b0c3534a",
        "filter": {
            "vnfInstanceSubscriptionFilter": {
                "vnfdIds": [
                    "dummy-vnfdId-1"
                ],
                "vnfProductsFromProviders": [
                    {
                        "vnfProvider": "dummy-vnfProvider-1",
                        "vnfProducts": [
                            {
                                "vnfProductName": "dummy-vnfProductName-1-1",
                                "versions": [
                                    {
                                        "vnfSoftwareVersion": 1.0,
                                        "vnfdVersions": [1.0, 2.0]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "vnfInstanceIds": [
                    "dummy-vnfInstanceId-1"
                ],
                "vnfInstanceNames": [
                    "dummy-vnfInstanceName-1"
                ]
            },
            "notificationTypes": [
                "AlarmNotification"
            ],
            "faultyResourceTypes": [
                "COMPUTE"
            ],
            "perceivedSeverities": [
                "WARNING"
            ],
            "eventTypes": [
                "EQUIPMENT_ALARM"
            ],
            "probableCauses": [
                "The server cannot be connected."
            ]
        },
        "callbackUri": "/nfvo/notify/alarm",
        "_links": {
            "self": {
                "href": "/vnffm/v1/subscriptions/"
                        "78a39661-60a8-4824-b989-88c1b0c3534a"
            }
        }
    }

    # Overwrite default attributes.
    fake_vnf_fm_sub.update(attrs)

    return fake_vnf_fm_sub


def get_vnffm_sub_data(vnf_fm_sub, columns=None):
    """Get the vnffm sub.

    :return:
        A tuple object sorted based on the name of the columns.
    """
    complex_attributes = ['filter', '_links']

    for attribute in complex_attributes:
        if vnf_fm_sub.get(attribute):
            vnf_fm_sub.update(
                {attribute: tacker_osc_utils.FormatComplexDataColumn(
                    vnf_fm_sub[attribute])})

    # return the list of data as per column order
    if columns:
        return tuple([vnf_fm_sub[key] for key in columns])

    return tuple([vnf_fm_sub[key] for key in sorted(
        vnf_fm_sub.keys())])
