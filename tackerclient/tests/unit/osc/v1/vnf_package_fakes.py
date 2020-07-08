# Copyright (C) 2019 NTT DATA
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


def vnf_package_obj(attrs=None, onboarded_state=False):
    """Create a fake vnf package.

    :param Dictionary attrs:
        A dictionary with all attributes
    :return:
        A FakeVnfPackage dict
    """
    attrs = attrs or {}

    # Set default attributes.
    fake_vnf_package = {"id": "60a6ac16-b50d-4e92-964b-b3cf98c7cf5c",
                        "_links": {"self": {"href": "string"},
                                   "packageContent": {"href": "string"}
                                   },
                        "onboardingState": "CREATED",
                        "operationalState": "DISABLED",
                        "usageState": "NOT_IN_USE",
                        "userDefinedData": {'key': 'value'}}

    if onboarded_state:
        fake_vnf_package = {"id": "60a6ac16-b50d-4e92-964b-b3cf98c7cf5c",
                            "vnfdId": "string",
                            "vnfProvider": "string",
                            "vnfProductName": "string",
                            "vnfSoftwareVersion": "string",
                            "vnfdVersion": "string",
                            "softwareImages": [
                                {
                                    "id": "string",
                                    "name": "string",
                                    "provider": "string",
                                    "version": "string",
                                    "checksum": {
                                        "algorithm": "string",
                                        "hash": "string"
                                    },
                                    "containerFormat": "AKI",
                                    "diskFormat": "AKI",
                                    "createdAt": "2015-06-03T18:49:19.000000",
                                    "minDisk": '0',
                                    "minRam": '0',
                                    "size": '0',
                                    "userMetadata": {},
                                    "imagePath": "string"
                                }
                            ],
                            "checksum": {
                                "algorithm": "string",
                                "hash": "string"
                            },
                            "onboardingState": "ONBOARDED",
                            "operationalState": "ENABLED",
                            "usageState": "IN_USE",
                            "userDefinedData": {'key': 'value'},
                            "_links": {
                                "self": {
                                    "href": "string"
                                },
                                "vnfd": {
                                    "href": "string"
                                },
                                "packageContent": {
                                    "href": "string"
                                }
                            },
                            "additionalArtifacts": [
                                {
                                    "artifactPath": "string",
                                    "metadata": {},
                                    "checksum": {
                                        "algorithm": "string",
                                        "hash": "string"
                                    }
                                }]
                            }

    # Overwrite default attributes.
    fake_vnf_package.update(attrs)
    return fake_vnf_package


def get_vnf_package_data(vnf_package_obj, **kwargs):
    """Get the vnf package data from a FakeVnfPackage dict object.

    :param vnf_package_obj:
        A FakeVnfPackage dict object
    :return:
        A list which may include the following values:
        [{'packageContent': {'href': 'string'}, 'self': {'href': 'string'},
        'vnfd': {'href': 'string'}}, '60a6ac16-b50d-4e92-964b-b3cf98c7cf5c',
        'CREATED', 'DISABLED', 'NOT_IN_USE', {'Test_key': 'Test_value'}]
    """
    complex_attributes = ['softwareImages', 'checksum', '_links',
                          'userDefinedData', 'additionalArtifacts']
    for attribute in complex_attributes:
        if vnf_package_obj.get(attribute):
            vnf_package_obj.update(
                {attribute: tacker_osc_utils.FormatComplexDataColumn(
                    vnf_package_obj[attribute])})

    if kwargs.get('list_action'):
        # In case of List VNF packages we get empty string as data for
        # 'vnfProductName' if onboardingState is CREATED. Hence to match
        # up with actual data we are adding here empty string.
        if not vnf_package_obj.get('vnfProductName'):
            vnf_package_obj['vnfProductName'] = ''

    if kwargs.get('columns'):
        # return the list of data as per column order
        return tuple([vnf_package_obj[key] for key in kwargs.get('columns')])

    return tuple([vnf_package_obj[key] for key in sorted(
        vnf_package_obj.keys())])


def create_vnf_packages(count=2, onboarded_vnf_package=False):
    """Create multiple fake vnf packages.

    :param Dictionary attrs:
        A dictionary with all attributes
    :param int count:
        The number of vnf_packages to fake
    :return:
        A list of fake vnf packages dictionary
    """
    vnf_packages = []
    for i in range(0, count):
        unique_id = uuidutils.generate_uuid()
        vnf_packages.append(vnf_package_obj(
            attrs={'id': unique_id}, onboarded_state=onboarded_vnf_package))
    return {'vnf_packages': vnf_packages}


def get_fake_update_vnf_package_obj(arglist):
    fake_update_vnf_package_dict = {}
    if '--user-data' in arglist:
        fake_update_vnf_package_dict.update(
            {"userDefinedData": {'Test_key': 'Test_value'}})
    if '--operational-state' in arglist:
        fake_update_vnf_package_dict.update({
            "operationalState": "DISABLED",
        })

    return fake_update_vnf_package_dict
