# Copyright (C) 2020 NTT DATA
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

from io import StringIO
import os
import sys
from unittest import mock

import ddt
from oslo_utils.fixture import uuidsentinel

from tackerclient.common import exceptions
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.osc.v1.vnflcm import vnflcm
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v1 import vnflcm_fakes
from tackerclient.v1_0 import client as proxy_client


class TestVnfLcm(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture

    def setUp(self):
        super(TestVnfLcm, self).setUp()
        self.url = client.TACKER_URL
        self.header = {'content-type': 'application/json'}
        self.app = mock.Mock()
        self.app_args = mock.Mock()
        self.client_manager = self.cs
        self.app.client_manager.tackerclient = self.client_manager


def _get_columns_vnflcm(action='create'):
    columns = ['ID', 'Instantiation State', 'VNF Instance Description',
               'VNF Instance Name', 'VNF Product Name', 'VNF Provider',
               'VNF Software Version', 'VNFD ID', 'VNFD Version', 'Links']
    if action == 'show':
        columns.extend(['Instantiated Vnf Info', 'VIM Connection Info'])
    if action == 'list':
        columns = [ele for ele in columns if ele not in
                   ['VNFD Version', 'VNF Instance Description']]
        columns.remove('Links')
    return columns


@ddt.ddt
class TestCreateVnfLcm(TestVnfLcm):

    def setUp(self):
        super(TestCreateVnfLcm, self).setUp()
        self.create_vnf_lcm = vnflcm.CreateVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm create')

    def test_create_no_args(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.create_vnf_lcm, [], [])

    @ddt.data({"optional_arguments": True, "instantiate": True},
              {"optional_arguments": False, "instantiate": False})
    @ddt.unpack
    def test_take_action(self, optional_arguments, instantiate):
        arglist = [uuidsentinel.vnf_package_vnfd_id]
        verifylist = [('vnfd_id', uuidsentinel.vnf_package_vnfd_id)]

        if optional_arguments:
            arglist.extend(['--name', 'test',
                            '--description', 'test'])
            verifylist.extend([('name', 'test'),
                               ('description', 'test')])

        # command param
        if instantiate:
            param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                          "instantiate_vnf_instance_param_sample.json")

            arglist.extend(['--I', param_file])
            verifylist.append(('I', param_file))

        parsed_args = self.check_parser(self.create_vnf_lcm, arglist,
                                        verifylist)

        json = vnflcm_fakes.vnf_instance_response()
        self.requests_mock.register_uri(
            'POST', os.path.join(self.url, 'vnflcm/v1/vnf_instances'),
            json=json, headers=self.header)

        if instantiate:
            self.requests_mock.register_uri(
                'POST', os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                                     json['id'], 'instantiate'),
                json={}, headers=self.header)

        sys.stdout = buffer = StringIO()
        actual_columns, data = (self.create_vnf_lcm.take_action(parsed_args))

        headers, attributes = vnflcm._get_columns(json)

        expected_message = (
            'VNF Instance ' + json['id'] + ' is created and instantiation '
                                           'request has been accepted.')
        if instantiate:
            self.assertEqual(expected_message, buffer.getvalue().strip())

        self.assertCountEqual(_get_columns_vnflcm(),
                              actual_columns)
        self.assertListItemsEqual(vnflcm_fakes.get_vnflcm_data(
            json, columns=attributes), data)


class TestShowVnfLcm(TestVnfLcm):

    def setUp(self):
        super(TestShowVnfLcm, self).setUp()
        self.show_vnf_lcm = vnflcm.ShowVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm show')

    def test_take_action(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response(
            instantiation_state='INSTANTIATED')

        arglist = [vnf_instance['id']]
        verifylist = [('vnf_instance', vnf_instance['id'])]

        # command param
        parsed_args = self.check_parser(self.show_vnf_lcm, arglist,
                                        verifylist)

        self.requests_mock.register_uri(
            'GET', os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                                vnf_instance['id']),
            json=vnf_instance, headers=self.header)

        columns, data = (self.show_vnf_lcm.take_action(parsed_args))
        self.assertCountEqual(_get_columns_vnflcm(action='show'),
                              columns)
        headers, attributes = vnflcm._get_columns(vnf_instance, action='show')
        self.assertListItemsEqual(
            vnflcm_fakes.get_vnflcm_data(vnf_instance, columns=attributes),
            data)


class TestListVnfLcm(TestVnfLcm):

    vnf_instances = vnflcm_fakes.create_vnf_instances(count=3)

    def setUp(self):
        super(TestListVnfLcm, self).setUp()
        self.list_vnf_instance = vnflcm.ListVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm list')

    def test_take_action(self):
        parsed_args = self.check_parser(self.list_vnf_instance, [], [])
        self.requests_mock.register_uri(
            'GET', os.path.join(self.url, 'vnflcm/v1/vnf_instances'),
            json=self.vnf_instances, headers=self.header)
        actual_columns, data = self.list_vnf_instance.take_action(parsed_args)

        headers, columns = tacker_osc_utils.get_column_definitions(
            vnflcm._attr_map, long_listing=True)

        expected_data = []
        for vnf_instance_obj in self.vnf_instances:
            expected_data.append(vnflcm_fakes.get_vnflcm_data(
                vnf_instance_obj, columns=columns, list_action=True))

        self.assertCountEqual(_get_columns_vnflcm(action='list'),
                              actual_columns)
        self.assertCountEqual(expected_data, list(data))


class TestInstantiateVnfLcm(TestVnfLcm):

    def setUp(self):
        super(TestInstantiateVnfLcm, self).setUp()
        self.instantiate_vnf_lcm = vnflcm.InstantiateVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm instantiate')

    def test_take_action(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                             "instantiate_vnf_instance_param_sample.json")

        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('instantiation_request_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.instantiate_vnf_lcm, arglist,
                                        verifylist)

        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           vnf_instance['id'], 'instantiate')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()
        with mock.patch.object(proxy_client.ClientBase,
                               '_handle_fault_response') as m:
            self.instantiate_vnf_lcm.take_action(parsed_args)
            # check no fault response is received
            self.assertNotCalled(m)
            self.assertEqual(
                'Instantiate request for VNF Instance ' + vnf_instance['id'] +
                ' has been accepted.', buffer.getvalue().strip())

    def test_take_action_vnf_instance_not_found(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                             "instantiate_vnf_instance_param_sample.json")
        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('instantiation_request_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.instantiate_vnf_lcm, arglist,
                                        verifylist)

        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           vnf_instance['id'], 'instantiate')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.instantiate_vnf_lcm.take_action,
                          parsed_args)

    def test_take_action_param_file_not_exists(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = "./not_exists.json"
        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('instantiation_request_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.instantiate_vnf_lcm, arglist,
                                        verifylist)

        ex = self.assertRaises(exceptions.InvalidInput,
                               self.instantiate_vnf_lcm.take_action,
                               parsed_args)

        expected_msg = ("Invalid input: File %s does not exist "
                        "or user does not have read privileges to it")
        self.assertEqual(expected_msg % sample_param_file, str(ex))

    @mock.patch("os.open")
    @mock.patch("os.access")
    def test_take_action_invalid_format_param_file(self, mock_open,
                                                   mock_access):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = "./invalid_param_file.json"
        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('instantiation_request_file', sample_param_file)]

        mock_open.return_value = "invalid_json_data"
        # command param
        parsed_args = self.check_parser(self.instantiate_vnf_lcm, arglist,
                                        verifylist)

        ex = self.assertRaises(exceptions.InvalidInput,
                               self.instantiate_vnf_lcm.take_action,
                               parsed_args)
        expected_msg = "Failed to load parameter file."
        self.assertIn(expected_msg, str(ex))


@ddt.ddt
class TestHealVnfLcm(TestVnfLcm):

    def setUp(self):
        super(TestHealVnfLcm, self).setUp()
        self.heal_vnf_lcm = vnflcm.HealVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm heal')

    @ddt.data((['--cause', 'test-cause', "--vnfc-instance",
                'vnfc-id-1', 'vnfc-id-2'],
               [('cause', 'test-cause'),
                ('vnfc_instance', ['vnfc-id-1', 'vnfc-id-2'])]),
              (['--cause', 'test-cause'],
               [('cause', 'test-cause')]),
              (["--vnfc-instance", 'vnfc-id-1', 'vnfc-id-2'],
               [('vnfc_instance', ['vnfc-id-1', 'vnfc-id-2'])]),
              ([], []))
    @ddt.unpack
    def test_take_action(self, arglist, verifylist):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        arglist.insert(0, vnf_instance['id'])
        verifylist.extend([('vnf_instance', vnf_instance['id'])])

        # command param
        parsed_args = self.check_parser(self.heal_vnf_lcm, arglist,
                                        verifylist)

        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           vnf_instance['id'], 'heal')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()
        result_error = self.heal_vnf_lcm.take_action(parsed_args)

        self.assertIsNone(result_error)
        actual_message = buffer.getvalue().strip()

        expected_message = ("Heal request for VNF Instance %s has been "
                            "accepted.") % vnf_instance['id']
        self.assertIn(expected_message, actual_message)

    def test_take_action_vnf_instance_not_found(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        arglist = [vnf_instance['id']]
        verifylist = [('vnf_instance', vnf_instance['id'])]

        # command param
        parsed_args = self.check_parser(self.heal_vnf_lcm, arglist,
                                        verifylist)

        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           vnf_instance['id'], 'heal')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.heal_vnf_lcm.take_action,
                          parsed_args)


@ddt.ddt
class TestTerminateVnfLcm(TestVnfLcm):

    def setUp(self):
        super(TestTerminateVnfLcm, self).setUp()
        self.terminate_vnf_instance = vnflcm.TerminateVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm terminate')

    @ddt.data({'termination_type': 'GRACEFUL', 'delete_vnf': True},
              {'termination_type': 'FORCEFUL', 'delete_vnf': False})
    @ddt.unpack
    def test_take_action(self, termination_type, delete_vnf):
        # argument 'delete_vnf' decides deletion of vnf instance post
        # termination.
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        arglist = ['--termination-type', termination_type, vnf_instance['id']]

        verifylist = [('termination_type', termination_type),
                      ('vnf_instance', vnf_instance['id'])]

        if delete_vnf:
            arglist.extend(['--D'])
            verifylist.extend([('D', True)])

        if termination_type == 'GRACEFUL':
            arglist.extend(['--graceful-termination-timeout', '60'])
            verifylist.append(('graceful_termination_timeout', 60))
        parsed_args = self.check_parser(self.terminate_vnf_instance, arglist,
                                        verifylist)
        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           vnf_instance['id'], 'terminate')

        with mock.patch.object(proxy_client.ClientBase,
                               '_handle_fault_response') as m:
            self.requests_mock.register_uri('POST', url, json={},
                                            headers=self.header)
            if delete_vnf:
                self.requests_mock.register_uri(
                    'GET', os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                                        vnf_instance['id']),
                    json=vnf_instance, headers=self.header)
                self.requests_mock.register_uri(
                    'DELETE', os.path.join(
                        self.url, 'vnflcm/v1/vnf_instances',
                        vnf_instance['id']), json={}, headers=self.header)

            sys.stdout = buffer = StringIO()
            result = self.terminate_vnf_instance.take_action(parsed_args)
            actual_message = buffer.getvalue().strip()

            expected_message = ("Terminate request for VNF Instance '%s'"
                                " has been accepted.") % vnf_instance['id']
            self.assertIn(expected_message, actual_message)

            if delete_vnf:
                expected_message = ("VNF Instance '%s' deleted successfully"
                                    % vnf_instance['id'])
                self.assertIn(expected_message, actual_message)

        self.assertIsNone(result)
        self.assertNotCalled(m)

    def test_take_action_terminate_and_delete_wait_failed(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        termination_type = 'GRACEFUL'
        arglist = ['--termination-type', termination_type, '--D',
                   '--graceful-termination-timeout', '5', vnf_instance['id']]

        verifylist = [('termination_type', termination_type), ('D', True),
                      ('graceful_termination_timeout', 5),
                      ('vnf_instance', vnf_instance['id'])]

        parsed_args = self.check_parser(self.terminate_vnf_instance, arglist,
                                        verifylist)
        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           vnf_instance['id'], 'terminate')

        self.requests_mock.register_uri('POST', url, json={},
                                        headers=self.header)
        # set the instantiateState to "INSTANTIATED", so that the
        # _wait_until_vnf_is_terminated will fail
        vnf_instance['instantiationState'] = 'INSTANTIATED'

        self.requests_mock.register_uri(
            'GET', os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                                vnf_instance['id']),
            json=vnf_instance, headers=self.header)

        sys.stdout = buffer = StringIO()
        with mock.patch.object(self.app.client_manager.tackerclient,
                               'delete_vnf_instance') as mock_delete:
            result = self.assertRaises(
                exceptions.CommandError,
                self.terminate_vnf_instance.take_action, parsed_args)

            actual_message = buffer.getvalue().strip()

            # Terminate vnf instance verification
            expected_message = ("Terminate request for VNF Instance '%s'"
                                " has been accepted.") % vnf_instance['id']
            self.assertIn(expected_message, actual_message)

            # Verify it fails to wait for termination before delete
            expected_message = ("Couldn't verify vnf instance is terminated "
                                "within '%(timeout)s' seconds. Unable to "
                                "delete vnf instance %(id)s"
                                % {'timeout': 15, 'id': vnf_instance['id']})

            self.assertIn(expected_message, str(result))
            self.assertNotCalled(mock_delete)

    def test_terminate_no_options(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.terminate_vnf_instance, [], [])

    def test_take_action_vnf_instance_not_found(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        termination_type = 'GRACEFUL'
        arglist = ['--termination-type', termination_type, '--D',
                   '--graceful-termination-timeout', '5', vnf_instance['id']]

        verifylist = [('termination_type', termination_type), ('D', True),
                      ('graceful_termination_timeout', 5),
                      ('vnf_instance', vnf_instance['id'])]

        parsed_args = self.check_parser(self.terminate_vnf_instance, arglist,
                                        verifylist)

        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           vnf_instance['id'], 'terminate')
        self.requests_mock.register_uri('POST', url, headers=self.header,
                                        status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.terminate_vnf_instance.take_action,
                          parsed_args)


class TestDeleteVnfLcm(TestVnfLcm):

    def setUp(self):
        super(TestDeleteVnfLcm, self).setUp()
        self.delete_vnf_instance = vnflcm.DeleteVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm delete')

        # Vnf Instance to delete
        self.vnf_instances = vnflcm_fakes.create_vnf_instances(count=3)

    def _mock_request_url_for_delete(self, vnf_index):
        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           self.vnf_instances[vnf_index]['id'])

        json = self.vnf_instances[vnf_index]

        self.requests_mock.register_uri('GET', url, json=json,
                                        headers=self.header)
        self.requests_mock.register_uri('DELETE', url,
                                        headers=self.header, json={})

    def test_delete_one_vnf_instance(self):
        arglist = [self.vnf_instances[0]['id']]
        verifylist = [('vnf_instances',
                       [self.vnf_instances[0]['id']])]

        parsed_args = self.check_parser(self.delete_vnf_instance, arglist,
                                        verifylist)

        self._mock_request_url_for_delete(0)
        sys.stdout = buffer = StringIO()
        result = self.delete_vnf_instance.take_action(parsed_args)
        self.assertIsNone(result)
        self.assertEqual(("Vnf instance '%s' deleted successfully")
                         % self.vnf_instances[0]['id'],
                         buffer.getvalue().strip())

    def test_delete_multiple_vnf_instance(self):
        arglist = []
        for vnf_pkg in self.vnf_instances:
            arglist.append(vnf_pkg['id'])
        verifylist = [('vnf_instances', arglist)]
        parsed_args = self.check_parser(self.delete_vnf_instance, arglist,
                                        verifylist)
        for i in range(0, 3):
            self._mock_request_url_for_delete(i)
        sys.stdout = buffer = StringIO()
        result = self.delete_vnf_instance.take_action(parsed_args)
        self.assertIsNone(result)
        self.assertEqual('All specified vnf instances are deleted '
                         'successfully', buffer.getvalue().strip())

    def test_delete_multiple_vnf_instance_exception(self):
        arglist = [
            self.vnf_instances[0]['id'],
            'xxxx-yyyy-zzzz',
            self.vnf_instances[1]['id'],
        ]
        verifylist = [('vnf_instances', arglist)]
        parsed_args = self.check_parser(self.delete_vnf_instance,
                                        arglist, verifylist)

        self._mock_request_url_for_delete(0)

        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           'xxxx-yyyy-zzzz')
        self.requests_mock.register_uri(
            'GET', url, exc=exceptions.ConnectionFailed)

        self._mock_request_url_for_delete(1)
        exception = self.assertRaises(exceptions.CommandError,
                                      self.delete_vnf_instance.take_action,
                                      parsed_args)

        self.assertEqual('Failed to delete 1 of 3 vnf instances.',
                         exception.message)


class TestUpdateVnfLcm(TestVnfLcm):
    def setUp(self):
        super(TestUpdateVnfLcm, self).setUp()
        self.update_vnf_lcm = vnflcm.UpdateVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm modify')

    def test_take_action(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                             "update_vnf_instance_param_sample.json")

        arglist = [vnf_instance['id'], '--I', sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('I', sample_param_file)]

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_lcm, arglist, verifylist)
        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_instances',
            vnf_instance['id'])

        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()
        self.update_vnf_lcm.take_action(parsed_args)

        actual_message = buffer.getvalue().strip()

        expected_message = ('Update vnf:' + vnf_instance['id'])

        self.assertEqual(expected_message, actual_message)

    def test_take_action_param_file_not_exists(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = "./not_exists.json"
        arglist = [vnf_instance['id'], '--I', sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('I', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.update_vnf_lcm, arglist,
                                        verifylist)

        self.assertRaises(exceptions.InvalidInput,
                          self.update_vnf_lcm.take_action, parsed_args)


@ddt.ddt
class TestScaleVnfLcm(TestVnfLcm):
    def setUp(self):
        super(TestScaleVnfLcm, self).setUp()
        self.scale_vnf_lcm = vnflcm.ScaleVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm scale')

    @ddt.data('SCALE_IN', 'SCALE_OUT')
    def test_take_action(self, scale_type):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                             "scale_vnf_instance_param_sample.json")

        arglist = [vnf_instance['id'],
                   '--aspect-id', uuidsentinel.aspect_id,
                   '--number-of-steps', '1',
                   '--type', scale_type,
                   '--additional-param-file', sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('aspect_id', uuidsentinel.aspect_id),
                      ('number_of_steps', 1),
                      ('type', scale_type),
                      ('additional_param_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.scale_vnf_lcm, arglist,
                                        verifylist)
        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_instances',
            vnf_instance['id'],
            'scale')

        self.requests_mock.register_uri(
            'POST', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()
        self.scale_vnf_lcm.take_action(parsed_args)

        actual_message = buffer.getvalue().strip()

        expected_message = ("Scale request for VNF Instance %s has been "
                            "accepted.") % vnf_instance['id']

        self.assertEqual(expected_message, actual_message)

    @ddt.data('SCALE_IN', 'SCALE_OUT')
    def test_take_action_no_param_file(self, scale_type):
        vnf_instance = vnflcm_fakes.vnf_instance_response()

        arglist = [vnf_instance['id'],
                   '--aspect-id', uuidsentinel.aspect_id,
                   '--number-of-steps', '1',
                   '--type', scale_type]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('aspect_id', uuidsentinel.aspect_id),
                      ('number_of_steps', 1),
                      ('type', scale_type)]

        parsed_args = self.check_parser(self.scale_vnf_lcm, arglist,
                                        verifylist)

        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           vnf_instance['id'], 'scale')

        self.requests_mock.register_uri(
            'POST', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()
        self.scale_vnf_lcm.take_action(parsed_args)

        actual_message = buffer.getvalue().strip()

        expected_message = ("Scale request for VNF Instance %s has been "
                            "accepted.") % vnf_instance['id']

        self.assertEqual(expected_message, actual_message)

    @ddt.data('SCALE_IN', 'SCALE_OUT')
    def test_take_action_param_file_not_exists(self, scale_type):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = "./not_exists.json"
        arglist = [vnf_instance['id'],
                   '--aspect-id', uuidsentinel.aspect_id,
                   '--number-of-steps', '2',
                   '--type', scale_type,
                   '--additional-param-file', sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('aspect_id', uuidsentinel.aspect_id),
                      ('number_of_steps', 2),
                      ('type', scale_type),
                      ('additional_param_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.scale_vnf_lcm, arglist,
                                        verifylist)

        ex = self.assertRaises(exceptions.InvalidInput,
                               self.scale_vnf_lcm.take_action, parsed_args)

        expected_msg = ("Invalid input: File %s does not exist "
                        "or user does not have read privileges to it")
        self.assertEqual(expected_msg % sample_param_file, str(ex))

    @ddt.data('SCALE_IN', 'SCALE_OUT')
    def test_take_action_vnf_instance_not_found(self, scale_type):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                             "update_vnf_instance_param_sample.json")
        arglist = [vnf_instance['id'],
                   '--aspect-id', uuidsentinel.aspect_id,
                   '--number-of-steps', '3',
                   '--type', scale_type,
                   '--additional-param-file', sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('aspect_id', uuidsentinel.aspect_id),
                      ('number_of_steps', 3),
                      ('type', scale_type),
                      ('additional_param_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.scale_vnf_lcm, arglist,
                                        verifylist)

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_instances',
            vnf_instance['id'])
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.scale_vnf_lcm.take_action,
                          parsed_args)
