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

from requests_mock.contrib import fixture as requests_mock_fixture
import testtools
from unittest import mock

from cliff import columns as cliff_columns


class FixturedTestCase(testtools.TestCase):
    client_fixture_class = None
    api_version = '1'

    def setUp(self):
        super(FixturedTestCase, self).setUp()
        self.app = mock.MagicMock()
        if self.client_fixture_class:
            self.requests_mock = self.useFixture(requests_mock_fixture.
                                                 Fixture())
            fix = self.client_fixture_class(self.requests_mock,
                                            api_version=self.api_version)
            self.cs = self.useFixture(fix).client

    def check_parser(self, cmd, args, verify_args):
        cmd_parser = cmd.get_parser('check_parser')
        try:
            parsed_args = cmd_parser.parse_args(args)
        except SystemExit:
            raise ParserException
        for av in verify_args:
            attr, value = av
            if attr:
                self.assertIn(attr, parsed_args)
                self.assertEqual(getattr(parsed_args, attr), value)
        return parsed_args

    def assertNotCalled(self, m, msg=None):
        """Assert a function was not called"""

        if m.called:
            if not msg:
                msg = 'method %s should not have been called' % m
            self.fail(msg)

    def assertListItemsEqual(self, expected, actual):
        """Assertion based on human_readable values of list items"""

        self.assertEqual(len(expected), len(actual))
        for col_expected, col_actual in zip(expected, actual):
            if isinstance(col_actual, tuple):
                self.assertListItemsEqual(col_expected, col_actual)
            elif isinstance(col_expected, cliff_columns.FormattableColumn):
                self.assertIsInstance(col_actual, col_expected.__class__)
                self.assertEqual(col_expected.human_readable(),
                                 col_actual.human_readable())
            else:
                self.assertEqual(col_expected, col_actual)


class ParserException(Exception):
    pass
