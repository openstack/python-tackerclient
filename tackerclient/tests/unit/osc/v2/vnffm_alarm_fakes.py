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


def create_vnf_fm_alarms(count=2):
    """Create multiple fake vnf packages.

    :param int count:
        The number of vnf_fm_alarms to fake
    :return:
        A list of fake vnf fm alarms dictionary
    """
    vnf_fm_alarms = []
    for i in range(0, count):
        unique_id = uuidutils.generate_uuid()
        vnf_fm_alarms.append(vnf_fm_alarm_response(attrs={'id': unique_id}))
    return vnf_fm_alarms


def vnf_fm_alarm_response(attrs=None, action=None):
    """Create a fake vnf fm alarm.

    :param Dictionary attrs:
        A dictionary with all attributes
    :return:
        A FakeVnfFmAlarm dict
    """

    if action == 'update':
        fake_vnf_fm_alarm = {
            "ackState": "UNACKNOWLEDGED"
        }
        return fake_vnf_fm_alarm

    attrs = attrs or {}
    # Set default attributes.
    fake_vnf_fm_alarm = {
        "id": "78a39661-60a8-4824-b989-88c1b0c3534a",
        "managedObjectId": "c61314d0-f583-4ab3-a457-46426bce02d3",
        "vnfcInstanceIds": "0e5f3086-4e79-47ed-a694-54c29155fa26",
        "rootCauseFaultyResource": {
            "faultyResource": {
                "vimConnectionId": "0d57e928-86a4-4445-a4bd-1634edae73f3",
                "resourceId": "4e6ccbe1-38ec-4b1b-a278-64de09ba01b3",
                "vimLevelResourceType": "OS::Nova::Server"
            },
            "faultyResourceType": "COMPUTE"
        },
        "alarmRaisedTime": "2021-09-03 10:21:03",
        "alarmChangedTime": "2021-09-04 10:21:03",
        "alarmClearedTime": "2021-09-05 10:21:03",
        "alarmAcknowledgedTime": "2021-09-06 10:21:03",
        "ackState": "UNACKNOWLEDGED",
        "perceivedSeverity": "WARNING",
        "eventTime": "2021-09-07 10:06:03",
        "eventType": "EQUIPMENT_ALARM",
        "faultType": "Fault Type",
        "probableCause": "The server cannot be connected.",
        "isRootCause": False,
        "correlatedAlarmIds": [
            "c88b624e-e997-4b17-b674-10ca2bab62e0",
            "c16d41fd-12e2-49a6-bb17-72faf702353f"
        ],
        "faultDetails": [
            "Fault",
            "Details"
        ],
        "_links": {
            "self": {
                "href": "/vnffm/v1/alarms/"
                        "78a39661-60a8-4824-b989-88c1b0c3534a"
            },
            "objectInstance": {
                "href": "/vnflcm/v1/vnf_instances/"
                        "0e5f3086-4e79-47ed-a694-54c29155fa26"
            }
        }
    }

    # Overwrite default attributes.
    fake_vnf_fm_alarm.update(attrs)

    return fake_vnf_fm_alarm


def get_vnffm_alarm_data(vnf_fm_alarm, columns=None):
    """Get the vnffm alarm.

    :return:
        A tuple object sorted based on the name of the columns.
    """
    complex_attributes = [
        'vnfcInstanceIds',
        'rootCauseFaultyResource',
        'correlatedAlarmIds',
        'faultDetails',
        '_links'
    ]

    for attribute in complex_attributes:
        if vnf_fm_alarm.get(attribute):
            vnf_fm_alarm.update(
                {attribute: tacker_osc_utils.FormatComplexDataColumn(
                    vnf_fm_alarm[attribute])})

    # return the list of data as per column order
    if columns:
        return tuple([vnf_fm_alarm[key] for key in columns])

    return tuple([vnf_fm_alarm[key] for key in sorted(
        vnf_fm_alarm.keys())])
