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


def vnf_package_obj(attrs=None):
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
                                   "vnfd": {"href": "string"},
                                   "packageContent": {"href": "string"}
                                   },
                        "onboardingState": "CREATED",
                        "operationalState": "DISABLED",
                        "usageState": "NOT_IN_USE",
                        "userDefinedData": None}

    # Overwrite default attributes.
    fake_vnf_package.update(attrs)
    return fake_vnf_package


def get_vnf_package_data(vnf_package=None):
    """Get the vnf package data from a FakeVnfPackage dict object.

    :param vnf_package:
        A FakeVnfPackage dict object
    :return:
        A tuple which may include the following values:
        (u"packageContent='{'href': 'string'}', self='{'href': 'string'}',
        vnfd='{'href': 'string'}'", '60a6ac16-b50d-4e92-964b-b3cf98c7cf5c',
        'CREATED', 'DISABLED', 'NOT_IN_USE', u"Test_key='Test_value'")
    """
    data_list = []
    if vnf_package is not None:
        for x in sorted(vnf_package.keys()):
                data_list.append(vnf_package[x])
    return tuple(data_list)
