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


def create_vnf_pm_jobs(count=2):
    """Create multiple fake vnf pm jobs.

    :param int count:
        The number of vnf_pm_jobs to fake
    :return:
        A list of fake vnf pm jobs dictionary
    """
    vnf_pm_jobs = []
    for i in range(0, count):
        unique_id = uuidutils.generate_uuid()
        vnf_pm_jobs.append(vnf_pm_job_response(attrs={'id': unique_id}))
    return {'vnf_pm_jobs': vnf_pm_jobs}


def vnf_pm_job_response(attrs=None, action=None):
    """Create a fake vnf pm job.

    :param Dictionary attrs:
        A dictionary with all attributes
    :return:
        A pm job dict
    """
    if action == 'update':
        fake_vnf_pm_job = {
            "callbackUri": "/nfvo/notify/job"
        }
        return fake_vnf_pm_job

    attrs = attrs or {}
    # Set default attributes.
    fake_vnf_pm_job = {
        "id": "2bb72d78-b1d9-48fe-8c64-332654ffeb5d",
        "objectType": "VNFC",
        "objectInstanceIds": [
            "object-instance-id-1"
        ],
        "subObjectInstanceIds": [
            "sub-object-instance-id-2"
        ],
        "criteria": {
            "performanceMetric": [
                "VCpuUsageMeanVnf.object-instance-id-1"
            ],
            "performanceMetricGroup": [
                "VirtualisedComputeResource"
            ],
            "collectionPeriod": 500,
            "reportingPeriod": 1000,
            "reportingBoundary": "2022/07/25 10:43:55"
        },
        "callbackUri": "/nfvo/notify/job",
        "reports": [{
            "href": "/vnfpm/v2/pm_jobs/2bb72d78-b1d9-48fe-8c64-332654ffeb5d/"
                    "reports/09d46aed-3ec2-45d9-bfa2-add431e069b3",
            "readyTime": "2022/07/25 10:43:55",
            "expiryTime": "2022/07/25 10:43:55",
            "fileSize": 9999
        }],
        "_links": {
            "self": {
                "href": "/vnfpm/v2/pm_jobs/"
                        "78a39661-60a8-4824-b989-88c1b0c3534a"
            },
            "objects": [{
                "href": "/vnflcm/v1/vnf_instances/"
                        "0e5f3086-4e79-47ed-a694-54c29155fa26"
            }]
        }
    }

    # Overwrite default attributes.
    fake_vnf_pm_job.update(attrs)

    return fake_vnf_pm_job


def get_vnfpm_job_data(vnf_pm_job, columns=None):
    """Get the vnfpm job.

    :return:
        A tuple object sorted based on the name of the columns.
    """
    complex_attributes = [
        'objectInstanceIds', 'subObjectInstanceIds',
        'criteria', 'reports', '_links',
        'authentication'
    ]

    for attribute in complex_attributes:
        if vnf_pm_job.get(attribute):
            vnf_pm_job.update(
                {attribute: tacker_osc_utils.FormatComplexDataColumn(
                    vnf_pm_job[attribute])})

    # return the list of data as per column order
    if columns is None:
        columns = sorted(vnf_pm_job.keys())
    return tuple([vnf_pm_job[key] for key in columns])
