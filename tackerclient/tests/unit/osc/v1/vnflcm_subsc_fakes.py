# Copyright (C) 2022 Nippon Telegraph and Telephone Corporation
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


def lccn_subsc_response(attrs=None):
    """Create a fake subscription.

    :param Dictionary attrs:
        A dictionary with all attributes
    :return:
        A subscription dict
    """
    attrs = attrs or {}
    id = uuidsentinel.lccn_subsc_id

    # Set default attributes.
    dummy_subscription = {
        "id": id,
        "filter": {
            "vnfInstanceSubscriptionFilter": {
                "vnfdIds": [
                    "dummy-vnfdId-1",
                    "dummy-vnfdId-2"
                ],
                "vnfProductsFromProviders": [
                    {
                        "vnfProvider": "dummy-vnfProvider-1",
                        "vnfProducts": [
                            {
                                "vnfProductName": "dummy-vnfProductName-1-1",
                                "versions": [
                                    {
                                        "vnfSoftwareVersion": "1.0",
                                        "vnfdVersions": ["1.0", "2.0"]
                                    },
                                    {
                                        "vnfSoftwareVersion": "1.1",
                                        "vnfdVersions": ["1.1", "2.1"]
                                    }
                                ]
                            },
                            {
                                "vnfProductName": "dummy-vnfProductName-1-2",
                                "versions": [
                                    {
                                        "vnfSoftwareVersion": "1.0",
                                        "vnfdVersions": ["1.0", "2.0"]
                                    },
                                    {
                                        "vnfSoftwareVersion": "1.1",
                                        "vnfdVersions": ["1.1", "2.1"]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "vnfProvider": "dummy-vnfProvider-2",
                        "vnfProducts": [
                            {
                                "vnfProductName": "dummy-vnfProductName-2-1",
                                "versions": [
                                    {
                                        "vnfSoftwareVersion": "1.0",
                                        "vnfdVersions": ["1.0", "2.0"]
                                    },
                                    {
                                        "vnfSoftwareVersion": "1.1",
                                        "vnfdVersions": ["1.1", "2.1"]
                                    }
                                ]
                            },
                            {
                                "vnfProductName": "dummy-vnfProductName-2-2",
                                "versions": [
                                    {
                                        "vnfSoftwareVersion": "1.0",
                                        "vnfdVersions": ["1.0", "2.0"]
                                    },
                                    {
                                        "vnfSoftwareVersion": "1.1",
                                        "vnfdVersions": ["1.1", "2.1"]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "vnfInstanceIds": [
                    "dummy-vnfInstanceId-1",
                    "dummy-vnfInstanceId-2"
                ],
                "vnfInstanceNames": [
                    "dummy-vnfInstanceName-1",
                    "dummy-vnfInstanceName-2"
                ]
            },
            "notificationTypes": [
                "VnfLcmOperationOccurrenceNotification",
                "VnfIdentifierCreationNotification",
                "VnfIdentifierDeletionNotification"
            ],
            "operationTypes": [
                "INSTANTIATE",
                "SCALE",
                "TERMINATE",
                "HEAL",
                "MODIFY_INFO",
                "CHANGE_EXT_CONN"
            ],
            "operationStates": [
                "COMPLETED",
                "FAILED",
                "FAILED_TEMP",
                "PROCESSING",
                "ROLLING_BACK",
                "ROLLED_BACK",
                "STARTING"
            ]
        },
        "callbackUri": "http://localhost:9990/notification/callback/test",
        "_links": {
            "self": {
                "href": "http://127.0.0.1:9890/vnflcm/v2/subscriptions/" + id
            }
        }
    }

    # Overwrite default attributes.
    dummy_subscription.update(attrs)

    return dummy_subscription


def get_subscription_data(subscription, list_action=False, columns=None):
    """Get the subscription data.

    :return:
        A tuple object sorted based on the name of the columns.
    """
    subsc = subscription.copy()
    complex_attributes = ['filter', '_links']
    for attribute in complex_attributes:
        if subsc.get(attribute):
            subsc.update(
                {attribute: tacker_osc_utils.FormatComplexDataColumn(
                    subsc[attribute])})

    if list_action:
        for item in ['filter', '_links']:
            subsc.pop(item)

    # return the list of data as per column order
    if columns:
        return tuple([subsc[key] for key in columns])

    return tuple([subsc[key] for key in sorted(
        subsc.keys())])


def create_subscriptions(count=2):
    """Create multiple fake subscriptions.

    :param count: The number of subscriptions to fake
    :return:
        A list of fake subscriptions dictionary
    """
    uri = "http://localhost:9990/notification/callback/"
    subscriptions = []
    for i in range(0, count):
        unique_id = uuidutils.generate_uuid()
        subscriptions.append(lccn_subsc_response(
            attrs={'id': unique_id,
                   'callbackUri': uri + str(i)}))
    return subscriptions
