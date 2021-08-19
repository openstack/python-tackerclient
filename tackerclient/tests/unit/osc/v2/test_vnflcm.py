# Copyright (C) 2021 Nippon Telegraph and Telephone Corporation
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

from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client


class TestVnfLcmV2(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture
    api_version = '2'

    def setUp(self):
        super(TestVnfLcmV2, self).setUp()

    def test_client_v2(self):
        self.assertEqual(self.cs.vnf_lcm_client.headers,
                         {'Version': '2.0.0'})
        self.assertEqual(self.cs.vnf_lcm_client.vnf_instances_path,
                         '/vnflcm/v2/vnf_instances')
        # check of other paths is omitted.
