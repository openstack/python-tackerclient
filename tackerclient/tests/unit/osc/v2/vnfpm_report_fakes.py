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

from tackerclient.osc import utils as tacker_osc_utils


def vnf_pm_report_response(attrs=None):
    """Create a fake vnf pm report.

    :param Dictionary attrs:
        A dictionary with all attributes
    :return:
        A pm report dict
    """

    attrs = attrs or {}
    # Set default attributes.
    fake_vnf_pm_report = {
        "entries": [
            {
                "objectType": "VNFC",
                "objectInstanceId": "2bb72d78-b1d9-48fe-8c64-332654ffeb5d",
                "subObjectInstanceId": "09d46aed-3ec2-45d9-bfa2-add431e069b3",
                "performanceMetric":
                    "VCpuUsagePeakVnf.2bb72d78-b1d9-48fe-8c64-332654ffeb5d,",
                "performanceValues": [
                    {
                        "timeStamp": "2022/07/27 08:58:58",
                        "value": "1.88",
                        "context": {
                            "key": "value"
                        }
                    }
                ]
            }
        ]
    }

    # Overwrite default attributes.
    fake_vnf_pm_report.update(attrs)

    return fake_vnf_pm_report


def get_vnfpm_report_data(vnf_pm_report, columns=None):
    """Get the vnfpm report.

    :return:
        A tuple object sorted based on the name of the columns.
    """
    attribute = 'entries'

    if vnf_pm_report.get(attribute):
        vnf_pm_report.update(
            {attribute: tacker_osc_utils.FormatComplexDataColumn(
                vnf_pm_report[attribute])})

    # return the list of data as per column order
    if columns is None:
        columns = sorted(vnf_pm_report.keys())
    return tuple([vnf_pm_report[key] for key in columns])
