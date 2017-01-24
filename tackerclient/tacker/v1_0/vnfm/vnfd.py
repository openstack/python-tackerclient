#
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

from __future__ import print_function

from oslo_serialization import jsonutils
import yaml

from tackerclient.common import utils
from tackerclient.i18n import _
from tackerclient.tacker import v1_0 as tackerV10


_VNFD = "vnfd"


class ListVNFD(tackerV10.ListCommand):
    """List VNFD that belong to a given tenant."""

    resource = _VNFD
    list_columns = ['id', 'name', 'template_source', 'description']

    def get_parser(self, prog_name):
        parser = super(ListVNFD, self).get_parser(prog_name)
        parser.add_argument(
            '--template-source',
            help=_("List VNFD with specified template source. Available \
                   options are 'onboarded' (default), 'inline' or 'all'"),
            action='store',
            default='onboarded')
        return parser

    def args2search_opts(self, parsed_args):
        search_opts = super(ListVNFD, self).args2search_opts(parsed_args)
        template_source = parsed_args.template_source
        if parsed_args.template_source:
            search_opts.update({'template_source': template_source})
        return search_opts


class ShowVNFD(tackerV10.ShowCommand):
    """Show information of a given VNFD."""

    resource = _VNFD


class CreateVNFD(tackerV10.CreateCommand):
    """Create a VNFD."""

    resource = _VNFD
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--vnfd-file', help=_('Specify VNFD file'))
        group.add_argument('--vnfd', help=_('Specify VNFD (DEPRECATED)'))
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the VNFD'))
        parser.add_argument(
            '--description',
            help=_('Set a description for the VNFD'))

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        vnfd = None
        if parsed_args.vnfd_file:
            with open(parsed_args.vnfd_file) as f:
                vnfd = f.read()
                vnfd = yaml.load(vnfd, Loader=yaml.SafeLoader)
        if parsed_args.vnfd:
            # TODO(sridhar_ram): Only file based input supported starting
            #       Ocata, remove all direct inputs in Pike
            utils.deprecate_warning(what="Direct VNFD template input",
                                    as_of="O",
                                    remove_in=1)
            vnfd = parsed_args.vnfd
            if isinstance(vnfd, str) or isinstance(vnfd, unicode):
                vnfd = yaml.load(vnfd, Loader=yaml.SafeLoader)

        if vnfd:
            body[self.resource]['attributes'] = {'vnfd': vnfd}

        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description'])
        return body


class DeleteVNFD(tackerV10.DeleteCommand):
    """Delete given VNFD(s)."""
    resource = _VNFD


class ShowTemplateVNFD(tackerV10.ShowCommand):
    """Show template of a given VNFD."""

    resource = _VNFD

    def run(self, parsed_args):
        self.log.debug('run(%s)', parsed_args)
        template = None
        data = self.get_data(parsed_args)
        try:
            attributes_index = data[0].index('attributes')
            attributes_json = data[1][attributes_index]
            template = jsonutils.loads(attributes_json).get('vnfd', None)
        except (IndexError, TypeError, ValueError) as e:
            self.log.debug('Data handling error: %s', str(e))
        print(template or _('Unable to display VNFD template!'))
