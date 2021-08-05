# Copyright 2013 Intel Corporation
# All Rights Reserved.
#
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

import logging

import testtools

from tackerclient.tacker import v1_0 as tackerV10


class TestCommandMeta(testtools.TestCase):
    def test_tacker_command_meta_defines_log(self):
        class FakeCommand(tackerV10.TackerCommand):
            pass

        self.assertTrue(hasattr(FakeCommand, 'log'))
        self.assertIsInstance(FakeCommand.log, logging.getLoggerClass())
        self.assertEqual(FakeCommand.log.name, __name__ + ".FakeCommand")

    def test_tacker_command_log_defined_explicitly(self):
        class FakeCommand(tackerV10.TackerCommand):
            log = None

        self.assertTrue(hasattr(FakeCommand, 'log'))
        self.assertIsNone(FakeCommand.log)
