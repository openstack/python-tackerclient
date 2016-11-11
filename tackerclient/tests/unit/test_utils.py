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

import testtools

from tackerclient.common import exceptions
from tackerclient.common import utils


class TestUtils(testtools.TestCase):
    def test_string_to_bool_true(self):
        self.assertTrue(utils.str2bool('true'))

    def test_string_to_bool_false(self):
        self.assertFalse(utils.str2bool('false'))

    def test_string_to_bool_None(self):
        self.assertIsNone(utils.str2bool(None))

    def test_string_to_dictionary(self):
        input_str = 'key1=value1,key2=value2'
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(expected, utils.str2dict(input_str))

    def test_none_string_to_dictionary(self):
        input_str = ''
        expected = {}
        self.assertEqual(expected, utils.str2dict(input_str))
        input_str = None
        expected = {}
        self.assertEqual(expected, utils.str2dict(input_str))

    def test_get_dict_item_properties(self):
        item = {'name': 'test_name', 'id': 'test_id'}
        fields = ('name', 'id')
        actual = utils.get_item_properties(item=item, fields=fields)
        self.assertEqual(('test_name', 'test_id'), actual)

    def test_get_object_item_properties_mixed_case_fields(self):
        class Fake(object):
            def __init__(self):
                self.id = 'test_id'
                self.name = 'test_name'
                self.test_user = 'test'

        fields = ('name', 'id', 'test user')
        mixed_fields = ('test user', 'ID')
        item = Fake()
        actual = utils.get_item_properties(item, fields, mixed_fields)
        self.assertEqual(('test_name', 'test_id', 'test'), actual)

    def test_get_object_item_desired_fields_differ_from_item(self):
        class Fake(object):
            def __init__(self):
                self.id = 'test_id_1'
                self.name = 'test_name'
                self.test_user = 'test'

        fields = ('name', 'id', 'test user')
        item = Fake()
        actual = utils.get_item_properties(item, fields)
        self.assertNotEqual(('test_name', 'test_id', 'test'), actual)

    def test_get_object_item_desired_fields_is_empty(self):
        class Fake(object):
            def __init__(self):
                self.id = 'test_id_1'
                self.name = 'test_name'
                self.test_user = 'test'

        fields = []
        item = Fake()
        actual = utils.get_item_properties(item, fields)
        self.assertEqual((), actual)

    def test_get_object_item_with_formatters(self):
        class Fake(object):
            def __init__(self):
                self.id = 'test_id'
                self.name = 'test_name'
                self.test_user = 'test'

        class FakeCallable(object):
            def __call__(self, *args, **kwargs):
                return 'pass'

        fields = ('name', 'id', 'test user', 'is_public')
        formatters = {'is_public': FakeCallable()}
        item = Fake()
        act = utils.get_item_properties(item, fields, formatters=formatters)
        self.assertEqual(('test_name', 'test_id', 'test', 'pass'), act)


class ImportClassTestCase(testtools.TestCase):

    def test_get_client_class_invalid_version(self):
        self.assertRaises(
            exceptions.UnsupportedVersion,
            utils.get_client_class, 'image', '2', {'image': '2'})


class ContainsKeyValue(object):
    """Checks whether a key/value pair is in a dict parameter.

    The ContainsKeyValue class is a helper for mock.assert_*()
    method. It enables strict check than the built in mock.ANY
    helper, and is the equivalent of the mox.ContainsKeyValue()
    function from the legacy mox library

    Example usage could be:

      mock_some_method.assert_called_once_with(
            "hello",
            ContainsKeyValue('foo', bar),
            mock.ANY,
            "world",
            ContainsKeyValue('hello', world))
    """
    def __init__(self, wantkey, wantvalue):
        self.wantkey = wantkey
        self.wantvalue = wantvalue

    def __eq__(self, other):
        try:
            return other[self.wantkey] == self.wantvalue
        except (KeyError, TypeError):
            return False

    def __ne__(self, other):
        try:
            return other[self.wantkey] != self.wantvalue
        except (KeyError, TypeError):
            return True

    def __repr__(self):
        return "<ContainsKeyValue: key " + str(self.wantkey) + \
               " and value " + str(self.wantvalue) + ">"
