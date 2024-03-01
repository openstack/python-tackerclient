# Copyright 2012 OpenStack Foundation.
# All Rights Reserved
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
#

import contextlib
import fixtures
import io
import sys
import testtools
from unittest import mock
import urllib
from urllib import parse as urlparse

from tackerclient.common import exceptions
from tackerclient import shell
from tackerclient.tacker import v1_0 as tackerV1_0
from tackerclient.tacker.v1_0 import TackerCommand
from tackerclient.tests.unit import test_utils
from tackerclient.v1_0 import client

API_VERSION = "1.0"
FORMAT = 'json'
TOKEN = 'testtoken'
ENDURL = 'localurl'


@contextlib.contextmanager
def capture_std_streams():
    fake_stdout, fake_stderr = io.StringIO(), io.StringIO()
    stdout, stderr = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = fake_stdout, fake_stderr
        yield fake_stdout, fake_stderr
    finally:
        sys.stdout, sys.stderr = stdout, stderr


class FakeStdout(io.IOBase):

    def __init__(self):
        self.content = []

    def write(self, text):
        self.content.append(text)

    def make_string(self):
        result = ''
        for line in self.content:
            result = result + line
        return result


class MyResp(object):
    def __init__(self, status_code, headers=None, reason=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.reason = reason


class MyApp(object):
    def __init__(self, _stdout):
        self.stdout = _stdout


def end_url(path, query=None, format=FORMAT):
    _url_str = ENDURL + "/v" + API_VERSION + path + "." + format
    return query and _url_str + "?" + query or _url_str


class MyUrlComparator(object):
    def __init__(self, lhs, client):
        self.lhs = lhs
        self.client = client

    def equals(self, rhs):
        lhsp = urlparse.urlparse(self.lhs)
        rhsp = urlparse.urlparse(rhs)

        lhs_qs = urlparse.parse_qsl(lhsp.query)
        rhs_qs = urlparse.parse_qsl(rhsp.query)

        return (lhsp.scheme == rhsp.scheme and
                lhsp.netloc == rhsp.netloc and
                lhsp.path == rhsp.path and
                len(lhs_qs) == len(rhs_qs) and
                set(lhs_qs) == set(rhs_qs))

    def __str__(self):
        if self.client and self.client.format != FORMAT:
            lhs_parts = self.lhs.split("?", 1)
            if len(lhs_parts) == 2:
                lhs = ("%s.%s?%s" % (lhs_parts[0][:-4],
                                     self.client.format,
                                     lhs_parts[1]))
            else:
                lhs = ("%s.%s" % (lhs_parts[0][:-4],
                                  self.client.format))
            return lhs
        return self.lhs

    def __repr__(self):
        return str(self)

    def __eq__(self, rhs):
        return self.equals(rhs)

    def __ne__(self, rhs):
        return not self.__eq__(rhs)


class MyComparator(object):
    def __init__(self, lhs, client):
        self.lhs = lhs
        self.client = client

    def _com_dict(self, lhs, rhs):
        if len(lhs) != len(rhs):
            return False
        for key, value in lhs.items():
            if key not in rhs:
                return False
            rhs_value = rhs[key]
            if not self._com(value, rhs_value):
                return False
        return True

    def _com_list(self, lhs, rhs):
        if len(lhs) != len(rhs):
            return False
        for lhs_value in lhs:
            if lhs_value not in rhs:
                return False
        return True

    def _com(self, lhs, rhs):
        if lhs is None:
            return rhs is None
        if isinstance(lhs, dict):
            if not isinstance(rhs, dict):
                return False
            return self._com_dict(lhs, rhs)
        if isinstance(lhs, list):
            if not isinstance(rhs, list):
                return False
            return self._com_list(lhs, rhs)
        if isinstance(lhs, tuple):
            if not isinstance(rhs, tuple):
                return False
            return self._com_list(lhs, rhs)
        return lhs == rhs

    def equals(self, rhs):
        if self.client:
            rhs = self.client.deserialize(rhs, 200)
        return self._com(self.lhs, rhs)

    def __repr__(self):
        if self.client:
            return self.client.serialize(self.lhs)
        return str(self.lhs)

    def __eq__(self, rhs):
        return self.equals(rhs)

    def __ne__(self, rhs):
        return not self.__eq__(rhs)


class CLITestV10Base(testtools.TestCase):

    format = 'json'
    test_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    id_field = 'id'

    def _find_resourceid(self, client, resource, name_or_id):
        return name_or_id

    def setUp(self, plurals={}):
        """Prepare the test environment."""
        super(CLITestV10Base, self).setUp()
        self.endurl = ENDURL
        self.fake_stdout = FakeStdout()
        self.useFixture(fixtures.MonkeyPatch('sys.stdout', self.fake_stdout))
        self.useFixture(fixtures.MonkeyPatch(
            'tackerclient.tacker.v1_0.find_resourceid_by_name_or_id',
            self._find_resourceid))
        self.useFixture(fixtures.MonkeyPatch(
            'tackerclient.tacker.v1_0.find_resourceid_by_id',
            self._find_resourceid))
        self.client = client.LegacyClient(token=TOKEN,
                                          endpoint_url=self.endurl)

    @mock.patch.object(TackerCommand, 'get_client')
    def _test_create_resource(self, resource, cmd,
                              name, myid, args,
                              position_names, position_values, mock_get,
                              tenant_id=None, get_client_called_count=1,
                              tags=None, admin_state_up=True, extra_body=None,
                              **kwargs):
        mock_get.return_value = self.client
        non_admin_status_resources = ['vim']
        if (resource in non_admin_status_resources):
            body = {resource: {}, }
        else:
            body = {resource: {'admin_state_up': admin_state_up, }, }
        if tenant_id:
            body[resource].update({'tenant_id': tenant_id})
        if tags:
            body[resource].update({'tags': tags})
        if extra_body:
            body[resource].update(extra_body)
        body[resource].update(kwargs)

        for i in range(len(position_names)):
            body[resource].update({position_names[i]: position_values[i]})
        ress = {resource:
                {self.id_field: myid}, }
        if name:
            ress[resource].update({'name': name})
        self.client.format = self.format
        resstr = self.client.serialize(ress)
        # url method body
        resource_plural = tackerV1_0._get_resource_plural(resource,
                                                          self.client)
        path = getattr(self.client, resource_plural + "_path")
        # Work around for LP #1217791. XML deserializer called from
        # MyComparator does not decodes XML string correctly.
        if self.format == 'json':
            _body = MyComparator(body, self.client)
            _content_type = 'application/json'
        else:
            _body = self.client.serialize(body)
            _content_type = 'application/zip'
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            mock_req.return_value = (MyResp(200), resstr)
            args.extend(['--request-format', self.format])
            cmd_parser = cmd.get_parser('create_' + resource)
            shell.run_command(cmd, cmd_parser, args)
            mock_req.assert_called_once_with(
                end_url(path, format=self.format), 'POST',
                body=_body,
                headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN),
                content_type=_content_type)
        self.assertEqual(get_client_called_count, mock_get.call_count)
        _str = self.fake_stdout.make_string()
        self.assertIn(myid, _str)
        if name:
            self.assertIn(name, _str)

    @mock.patch.object(TackerCommand, 'get_client')
    def _test_list_columns(self, cmd, resources_collection,
                           resources_out, mock_get,
                           args=['-f', 'json']):
        mock_get.return_value = self.client
        self.client.format = self.format
        resstr = self.client.serialize(resources_out)

        path = getattr(self.client, resources_collection + "_path")
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            mock_req.return_value = (MyResp(200), resstr)
            args.extend(['--request-format', self.format])
            cmd_parser = cmd.get_parser("list_" + resources_collection)
            shell.run_command(cmd, cmd_parser, args)
            mock_req.assert_called_once_with(
                end_url(path, format=self.format), 'GET',
                body=None,
                headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN),
                content_type='application/json')
        mock_get.assert_called_once_with()

    def _test_list_resources(self, resources, cmd, detail=False, tags=[],
                             fields_1=[], fields_2=[], page_size=None,
                             sort_key=[], sort_dir=[], response_contents=None,
                             base_args=None, path=None,
                             template_source=None):
        if response_contents is None:
            contents = [{self.id_field: 'myid1', },
                        {self.id_field: 'myid2', }, ]
        else:
            contents = response_contents
        reses = {resources: contents}
        self.client.format = self.format
        resstr = self.client.serialize(reses)
        # url method body
        query = ""
        args = base_args if base_args is not None else []
        if detail:
            args.append('-D')
        args.extend(['--request-format', self.format])
        if fields_1:
            for field in fields_1:
                args.append('--fields')
                args.append(field)
        if template_source is not None:
            args.append("--template-source")
            args.append(template_source)
            query += 'template_source=' + template_source

        if tags:
            args.append('--')
            args.append("--tag")
        for tag in tags:
            args.append(tag)
            if isinstance(tag, str):
                tag = urllib.quote(tag.encode('utf-8'))
            if query:
                query += "&tag=" + tag
            else:
                query = "tag=" + tag
        if (not tags) and fields_2:
            args.append('--')
        if fields_2:
            args.append("--fields")
            for field in fields_2:
                args.append(field)
        if detail:
            query = query and query + '&verbose=True' or 'verbose=True'
        fields_1.extend(fields_2)
        for field in fields_1:
            if query:
                query += "&fields=" + field
            else:
                query = "fields=" + field
        if page_size:
            args.append("--page-size")
            args.append(str(page_size))
            if query:
                query += "&limit=%s" % page_size
            else:
                query = "limit=%s" % page_size
        if sort_key:
            for key in sort_key:
                args.append('--sort-key')
                args.append(key)
                if query:
                    query += '&'
                query += 'sort_key=%s' % key
        if sort_dir:
            len_diff = len(sort_key) - len(sort_dir)
            if len_diff > 0:
                sort_dir += ['asc'] * len_diff
            elif len_diff < 0:
                sort_dir = sort_dir[:len(sort_key)]
            for dir in sort_dir:
                args.append('--sort-dir')
                args.append(dir)
                if query:
                    query += '&'
                query += 'sort_dir=%s' % dir
        if path is None:
            path = getattr(self.client, resources + "_path")
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            mock_req.return_value = (MyResp(200), resstr)
            with mock.patch.object(TackerCommand, 'get_client') as mock_get:
                mock_get.return_value = self.client
                cmd_parser = cmd.get_parser("list_" + resources)
                shell.run_command(cmd, cmd_parser, args)
                mock_req.assert_called_once_with(
                    MyUrlComparator(end_url(path, query, format=self.format),
                                    self.client),
                    'GET',
                    body=None,
                    headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN),
                    content_type='application/json')
        _str = self.fake_stdout.make_string()
        if response_contents is None:
            self.assertIn('myid1', _str)
        return _str

    @mock.patch.object(TackerCommand, 'get_client')
    def _test_list_sub_resources(self, resources, api_resource, cmd, myid,
                                 mock_get, detail=False,
                                 tags=[], fields_1=[], fields_2=[],
                                 page_size=None, sort_key=[], sort_dir=[],
                                 response_contents=None, base_args=None,
                                 path=None):
        mock_get.return_value = self.client
        if response_contents is None:
            contents = [{self.id_field: 'myid1', },
                        {self.id_field: 'myid2', }, ]
        else:
            contents = response_contents
        reses = {api_resource: contents}
        self.client.format = self.format
        resstr = self.client.serialize(reses)
        # url method body
        query = ""
        args = base_args if base_args is not None else []
        if detail:
            args.append('-D')
        args.extend(['--request-format', self.format])
        if fields_1:
            for field in fields_1:
                args.append('--fields')
                args.append(field)

        if tags:
            args.append('--')
            args.append("--tag")
        for tag in tags:
            args.append(tag)
            if isinstance(tag, str):
                tag = urllib.quote(tag.encode('utf-8'))
            if query:
                query += "&tag=" + tag
            else:
                query = "tag=" + tag
        if (not tags) and fields_2:
            args.append('--')
        if fields_2:
            args.append("--fields")
            for field in fields_2:
                args.append(field)
        if detail:
            query = query and query + '&verbose=True' or 'verbose=True'
        fields_1.extend(fields_2)
        for field in fields_1:
            if query:
                query += "&fields=" + field
            else:
                query = "fields=" + field
        if page_size:
            args.append("--page-size")
            args.append(str(page_size))
            if query:
                query += "&limit=%s" % page_size
            else:
                query = "limit=%s" % page_size
        if sort_key:
            for key in sort_key:
                args.append('--sort-key')
                args.append(key)
                if query:
                    query += '&'
                query += 'sort_key=%s' % key
        if sort_dir:
            len_diff = len(sort_key) - len(sort_dir)
            if len_diff > 0:
                sort_dir += ['asc'] * len_diff
            elif len_diff < 0:
                sort_dir = sort_dir[:len(sort_key)]
            for dir in sort_dir:
                args.append('--sort-dir')
                args.append(dir)
                if query:
                    query += '&'
                query += 'sort_dir=%s' % dir
        if path is None:
            path = getattr(self.client, resources + "_path")
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            mock_req.return_value = (MyResp(200), resstr)
            comparator = MyUrlComparator(
                end_url(path % myid, query=query, format=self.format),
                self.client)
            args.extend(['--request-format', self.format])
            cmd_parser = cmd.get_parser("list_" + resources)
            shell.run_command(cmd, cmd_parser, args)
            mock_req.assert_called_once_with(
                comparator, 'GET',
                body=None,
                headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN),
                content_type='application/json')
        _str = self.fake_stdout.make_string()
        if response_contents is None:
            self.assertIn('myid1', _str)
        return _str

    # TODO(gongysh) add pagination unit test BUG 1633255
    # def _test_list_sub_resources_with_pagination(
    #      self, resources, api_resource, cmd, myid):
    #     self.mox.StubOutWithMock(cmd, "get_client")
    #     self.mox.StubOutWithMock(self.client.httpclient, "request")
    #     cmd.get_client().MultipleTimes().AndReturn(self.client)
    #     path = getattr(self.client, resources + "_path")
    #     fake_query = "marker=myid2&limit=2"
    #     reses1 = {api_resource: [{'id': 'myid1', },
    #                              {'id': 'myid2', }],
    #               '%s_links' % api_resource: [
    #                   {'href': end_url(path % myid, fake_query),
    #                    'rel': 'next'}]
    #               }
    #     reses2 = {api_resource: [{'id': 'myid3', },
    #                              {'id': 'myid4', }]}
    #     self.client.format = self.format
    #     resstr1 = self.client.serialize(reses1)
    #     resstr2 = self.client.serialize(reses2)
    #     self.client.httpclient.request(
    #         end_url(path % myid, "", format=self.format), 'GET',
    #         body=None,
    #         headers=mox.ContainsKeyValue(
    #             'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr1))
    #     self.client.httpclient.request(
    #         MyUrlComparator(end_url(path % myid, fake_query,
    #                                 format=self.format), self.client), 'GET',
    #         body=None, headers=mox.ContainsKeyValue(
    #             'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr2))
    #     self.mox.ReplayAll()
    #     cmd_parser = cmd.get_parser("list_" + resources)
    #     args = [myid, '--request-format', self.format]
    #     shell.run_command(cmd, cmd_parser, args)
    #     self.mox.VerifyAll()
    #     self.mox.UnsetStubs()

    # def _test_list_resources_with_pagination(self, resources, cmd):
    #     self.mox.StubOutWithMock(cmd, "get_client")
    #     self.mox.StubOutWithMock(self.client.httpclient, "request")
    #     cmd.get_client().MultipleTimes().AndReturn(self.client)
    #     path = getattr(self.client, resources + "_path")
    #     fake_query = "marker=myid2&limit=2"
    #     reses1 = {resources: [{'id': 'myid1', },
    #                           {'id': 'myid2', }],
    #               '%s_links' % resources: [
    #                   {'href': end_url(path, fake_query),
    #                    'rel': 'next'}]}
    #     reses2 = {resources: [{'id': 'myid3', },
    #                           {'id': 'myid4', }]}
    #     self.client.format = self.format
    #     resstr1 = self.client.serialize(reses1)
    #     resstr2 = self.client.serialize(reses2)
    #     self.client.httpclient.request(
    #         end_url(path, "", format=self.format), 'GET',
    #         body=None,
    #         headers=mox.ContainsKeyValue(
    #             'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr1))
    #     self.client.httpclient.request(
    #         MyUrlComparator(end_url(path, fake_query, format=self.format),
    #                         self.client), 'GET', body=None,
    #         headers=mox.ContainsKeyValue(
    #             'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr2))
    #     self.mox.ReplayAll()
    #     cmd_parser = cmd.get_parser("list_" + resources)
    #     args = ['--request-format', self.format]
    #     shell.run_command(cmd, cmd_parser, args)
    #     self.mox.VerifyAll()
    #     self.mox.UnsetStubs()

    @mock.patch.object(TackerCommand, 'get_client')
    def _test_update_resource(self, resource, cmd, myid, args, extrafields,
                              mock_get, get_client_called_count=1):
        mock_get.return_value = self.client
        body = {resource: extrafields}
        path = getattr(self.client, resource + "_path")
        self.client.format = self.format
        # Work around for LP #1217791. XML deserializer called from
        # MyComparator does not decodes XML string correctly.
        if self.format == 'json':
            _body = MyComparator(body, self.client)
            _content_type = 'application/json'
        else:
            _body = self.client.serialize(body)
            _content_type = 'application/zip'
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            comparator = MyUrlComparator(
                end_url(path % myid, format=self.format), self.client)
            mock_req.return_value = (MyResp(204), None)
            args.extend(['--request-format', self.format])
            cmd_parser = cmd.get_parser("update_" + resource)
            shell.run_command(cmd, cmd_parser, args)
            mock_req.assert_called_once_with(
                comparator,
                'PUT',
                body=_body,
                headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN),
                content_type=_content_type)

        self.assertEqual(get_client_called_count, mock_get.call_count)
        _str = self.fake_stdout.make_string()
        self.assertIn(myid, _str)

    def _test_show_resource(self, resource, cmd, myid, args, fields=[]):
        with mock.patch.object(cmd, 'get_client') as mock_get:
            mock_get.return_value = self.client
            query = "&".join(["fields=%s" % field for field in fields])
            expected_res = {resource:
                            {self.id_field: myid,
                             'name': 'myname', }, }
            self.client.format = self.format
            resstr = self.client.serialize(expected_res)
            path = getattr(self.client, resource + "_path")
            with mock.patch.object(self.client.httpclient, 'request') as\
                    mock_req:
                mock_req.return_value = (MyResp(200), resstr)
                args.extend(['--request-format', self.format])
                cmd_parser = cmd.get_parser("show_" + resource)
                shell.run_command(cmd, cmd_parser, args)
                mock_req.assert_called_once_with(
                    end_url(path % myid, query, format=self.format), 'GET',
                    body=None,
                    headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN),
                    content_type='application/json')
            _str = self.fake_stdout.make_string()
            mock_get.assert_called_once_with()
            self.assertIn(myid, _str)
            self.assertIn('myname', _str)

    @mock.patch.object(TackerCommand, 'get_client')
    def _test_delete_resource(self, resource, cmd, myid, args, mock_get):
        deleted_msg = {'vnf': 'delete initiated'}
        mock_get.return_value = self.client
        path = getattr(self.client, resource + "_path")
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            mock_req.return_value = (MyResp(204), None)
            args.extend(['--request-format', self.format])
            cmd_parser = cmd.get_parser("delete_" + resource)
            shell.run_command(cmd, cmd_parser, args)
            if '--force' in args:
                body_str = '{"' + resource + \
                           '": {"attributes": {"force": true}}}'
                mock_req.assert_called_once_with(
                    end_url(path % myid, format=self.format), 'DELETE',
                    body=body_str,
                    headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN),
                    content_type='application/json')
            else:
                mock_req.assert_called_once_with(
                    end_url(path % myid, format=self.format), 'DELETE',
                    body=None,
                    headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN),
                    content_type='application/json')
        mock_get.assert_called_once_with()
        _str = self.fake_stdout.make_string()
        msg = 'All specified %(resource)s(s) %(msg)s successfully\n' % {
            'msg': deleted_msg.get(resource, 'deleted'),
            'resource': resource}
        self.assertEqual(msg, _str)

    @mock.patch.object(TackerCommand, 'get_client')
    def _test_update_resource_action(self, resource, cmd, myid, action, args,
                                     body, mock_get, retval=None):
        mock_get.return_value = self.client
        path = getattr(self.client, resource + "_path")
        path_action = '%s/%s' % (myid, action)
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            mock_req.return_value = (MyResp(204), retval)
            args.extend(['--request-format', self.format])
            cmd_parser = cmd.get_parser("delete_" + resource)
            shell.run_command(cmd, cmd_parser, args)
            mock_req.assert_called_once_with(
                end_url(path % path_action, format=self.format), 'PUT',
                body=MyComparator(body, self.client),
                headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN),
                content_type='application/json')
        _str = self.fake_stdout.make_string()
        self.assertIn(myid, _str)


class ClientV1TestJson(CLITestV10Base):
    def test_do_request_unicode(self):
        self.client.format = self.format
        unicode_text = '\u7f51\u7edc'
        action = '/test'
        params = {'test': unicode_text}
        body = params
        expect_body = self.client.serialize(body)
        self.client.httpclient.auth_token = unicode_text
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            mock_req.return_value = (MyResp(200), expect_body)
            res_body = self.client.do_request('PUT', action, body=body,
                                              params=params)
            expected_uri = 'localurl/v1.0/test.json?test=%E7%BD%91%E7%BB%9C'
            mock_req.assert_called_with(
                expected_uri, 'PUT', body=expect_body,
                headers={'X-Auth-Token': unicode_text,
                         'User-Agent': 'python-tackerclient'},
                content_type='application/json')
        # test response with unicode
        self.assertEqual(res_body, body)

    def test_do_request_error_without_response_body(self):
        self.client.format = self.format
        params = {'test': 'value'}
        expect_query = urlparse.urlencode(params)
        self.client.httpclient.auth_token = 'token'
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            mock_req.return_value = (MyResp(400, reason='An error'), '')
            self.client.httpclient.request(
                end_url('/test', query=expect_query, format=self.format),
                'PUT', body='',
                headers={'X-Auth-Token': 'token'}
            )
            error = self.assertRaises(exceptions.TackerClientException,
                                      self.client.do_request, 'PUT', '/test',
                                      body='', params=params)
            self.assertEqual("400-tackerFault", str(error))


class CLITestV10ExceptionHandler(CLITestV10Base):

    def _test_exception_handler_v10(
            self, expected_exception, status_code, expected_msg,
            error_type=None, error_msg=None, error_detail=None,
            error_content=None):
        if error_content is None:
            error_content = {'TackerError': {'type': error_type,
                                             'message': error_msg,
                                             'detail': error_detail}}

        e = self.assertRaises(expected_exception,
                              client.exception_handler_v10,
                              status_code, error_content)
        self.assertEqual(status_code, e.status_code)
        self.assertEqual(expected_exception.__name__,
                         e.__class__.__name__)

        if expected_msg is None:
            if error_detail:
                expected_msg = '\n'.join([error_msg, error_detail])
            else:
                expected_msg = error_msg
        self.assertEqual(expected_msg, e.message)

    def test_exception_handler_v10_unknown_error_to_per_code_exception(self):
        for status_code, client_exc in exceptions.HTTP_EXCEPTION_MAP.items():
            error_msg = 'Unknown error'
            error_detail = 'This is detail'
            self._test_exception_handler_v10(
                client_exc, status_code,
                error_msg + '\n' + error_detail,
                'UnknownError', error_msg, error_detail)

    def test_exception_handler_v10_tacker_unknown_status_code(self):
        error_msg = 'Unknown error'
        error_detail = 'This is detail'
        self._test_exception_handler_v10(
            exceptions.TackerClientException, 501,
            error_msg + '\n' + error_detail,
            'UnknownError', error_msg, error_detail)

    def test_exception_handler_v10_bad_tacker_error(self):
        error_content = {'TackerError': {'unknown_key': 'UNKNOWN'}}
        self._test_exception_handler_v10(
            exceptions.TackerClientException, 500,
            expected_msg={'unknown_key': 'UNKNOWN'},
            error_content=error_content)

    def test_exception_handler_v10_error_dict_contains_message(self):
        error_content = {'message': 'This is an error message'}
        self._test_exception_handler_v10(
            exceptions.TackerClientException, 500,
            expected_msg='500-tackerFault',
            error_content=error_content)

    def test_exception_handler_v10_error_dict_not_contain_message(self):
        error_content = 'tackerFault'
        expected_msg = '%s-%s' % (500, error_content)
        self._test_exception_handler_v10(
            exceptions.TackerClientException, 500,
            expected_msg=expected_msg,
            error_content=error_content)

    def test_exception_handler_v10_default_fallback(self):
        error_content = 'This is an error message'
        expected_msg = '%s-%s' % (500, error_content)
        self._test_exception_handler_v10(
            exceptions.TackerClientException, 500,
            expected_msg=expected_msg,
            error_content=error_content)

    def test_exception_handler_v10_tacker_etsi_error(self):
        """Test ETSI error response"""

        known_error_map = [
            ({
                "status": "status 1",
                "detail": "sample 1"
            }, 400),
            ({
                "status": "status 2",
                "detail": "sample 2"
            }, 404),
            ({
                "status": "status 3",
                "detail": "sample 3"
            }, 409)
        ]

        for error_content, status_code in known_error_map:
            self._test_exception_handler_v10(
                exceptions.TackerClientException, status_code,
                expected_msg=error_content['detail'],
                error_content=error_content)
