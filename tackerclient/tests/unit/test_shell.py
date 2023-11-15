# Copyright (C) 2013 Yahoo! Inc.
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

import argparse
import fixtures
import io
import logging
import os
import re
import sys
import testtools
from testtools import matchers
from unittest import mock

from keystoneclient import session

from tackerclient.common import clientmanager
from tackerclient import shell as openstack_shell


DEFAULT_USERNAME = 'username'
DEFAULT_PASSWORD = 'password'
DEFAULT_TENANT_ID = 'tenant_id'
DEFAULT_TENANT_NAME = 'tenant_name'
DEFAULT_AUTH_URL = 'http://127.0.0.1:5000/v1.0/'
DEFAULT_TOKEN = '3bcc3d3a03f44e3d8377f9247b0ad155'
DEFAULT_URL = 'http://tacker.example.org:9890/'
DEFAULT_API_VERSION = '1.0'


class ShellTest(testtools.TestCase):

    FAKE_ENV = {
        'OS_USERNAME': DEFAULT_USERNAME,
        'OS_PASSWORD': DEFAULT_PASSWORD,
        'OS_TENANT_ID': DEFAULT_TENANT_ID,
        'OS_TENANT_NAME': DEFAULT_TENANT_NAME,
        'OS_AUTH_URL': DEFAULT_AUTH_URL}

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        super(ShellTest, self).setUp()
        for var in self.FAKE_ENV:
            self.useFixture(
                fixtures.EnvironmentVariable(
                    var, self.FAKE_ENV[var]))

    def shell(self, argstr, check=False):
        orig = (sys.stdout, sys.stderr)
        clean_env = {}
        _old_env, os.environ = os.environ, clean_env.copy()
        try:
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            _shell = openstack_shell.TackerShell(DEFAULT_API_VERSION)
            _shell.run(argstr.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertEqual(exc_value.code, 0)
        finally:
            stdout = sys.stdout.getvalue()
            stderr = sys.stderr.getvalue()
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout, sys.stderr = orig
            os.environ = _old_env
        return stdout, stderr

    def test_run_unknown_command(self):
        self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))
        stdout, stderr = self.shell('fake', check=True)
        self.assertFalse(stdout)
        self.assertEqual("Unknown command ['fake']", stderr.strip())

    def test_help(self):
        required = 'usage:'
        help_text, stderr = self.shell('help')
        self.assertThat(
            help_text,
            matchers.MatchesRegex(required))
        self.assertFalse(stderr)

    def test_help_on_subcommand(self):
        required = [
            '.*?^usage: .* vim-list']
        stdout, stderr = self.shell('help vim-list')
        for r in required:
            self.assertThat(
                stdout,
                matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))
        self.assertFalse(stderr)

    def test_help_command(self):
        required = 'usage:'
        help_text, stderr = self.shell('help vim-create')
        self.assertThat(
            help_text,
            matchers.MatchesRegex(required))
        self.assertFalse(stderr)

    def test_unknown_auth_strategy(self):
        self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))
        stdout, stderr = self.shell('--os-auth-strategy fake '
                                    'vim-list')
        self.assertFalse(stdout)

    def test_auth(self):
        with mock.patch.object(openstack_shell.TackerShell,
                               'run_subcommand'), \
                mock.patch.object(session, 'Session'), \
                mock.patch.object(clientmanager, 'ClientManager') as mock_cmgr:

            shell = openstack_shell.TackerShell(DEFAULT_API_VERSION)
            shell.options = mock.Mock()
            auth_session = shell._get_keystone_session()

            cmdline = ('--os-username test '
                       '--os-password test '
                       '--os-tenant-name test '
                       '--os-auth-url http://127.0.0.1:5000/ '
                       '--os-auth-strategy keystone vim-list')
            shell.authenticate_user()
            shell.run(cmdline.split())

        mock_cmgr.assert_called_with(
            raise_errors=False, retries=0, timeout=None,
            token='', url='', auth_url='http://127.0.0.1:5000/',
            tenant_name='test', tenant_id='tenant_id',
            username='test', user_id='',
            password='test', region_name='',
            api_version={'nfv-orchestration': '1.0'},
            auth_strategy='keystone',
            service_type='nfv-orchestration',
            endpoint_type='publicURL', insecure=False, ca_cert=None,
            log_credentials=True, session=auth_session, auth=auth_session.auth)

    def test_build_option_parser(self):
        tacker_shell = openstack_shell.TackerShell(DEFAULT_API_VERSION)
        result = tacker_shell.build_option_parser('descr', DEFAULT_API_VERSION)
        self.assertIsInstance(result, argparse.ArgumentParser)

    @mock.patch.object(openstack_shell.TackerShell, 'run')
    def test_main_with_unicode(self, mock_run):
        mock_run.return_value = 0
        unicode_text = '\u7f51\u7edc'
        argv = ['net-list', unicode_text, unicode_text.encode('utf-8')]
        ret = openstack_shell.main(argv=argv)
        mock_run.assert_called_once_with(['net-list', unicode_text,
                                          unicode_text])
        self.assertEqual(0, ret)

    def test_endpoint_option(self):
        shell = openstack_shell.TackerShell(DEFAULT_API_VERSION)
        parser = shell.build_option_parser('descr', DEFAULT_API_VERSION)

        # Neither $OS_ENDPOINT_TYPE nor --endpoint-type
        namespace = parser.parse_args([])
        self.assertEqual('publicURL', namespace.endpoint_type)

        # --endpoint-type but not $OS_ENDPOINT_TYPE
        namespace = parser.parse_args(['--endpoint-type=admin'])
        self.assertEqual('admin', namespace.endpoint_type)

    def test_endpoint_environment_variable(self):
        fixture = fixtures.EnvironmentVariable("OS_ENDPOINT_TYPE",
                                               "public")
        self.useFixture(fixture)

        shell = openstack_shell.TackerShell(DEFAULT_API_VERSION)
        parser = shell.build_option_parser('descr', DEFAULT_API_VERSION)

        # $OS_ENDPOINT_TYPE but not --endpoint-type
        namespace = parser.parse_args([])
        self.assertEqual("public", namespace.endpoint_type)

        # --endpoint-type and $OS_ENDPOINT_TYPE
        namespace = parser.parse_args(['--endpoint-type=admin'])
        self.assertEqual('admin', namespace.endpoint_type)
