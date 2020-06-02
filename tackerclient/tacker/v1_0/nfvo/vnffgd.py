# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import yaml

from oslo_serialization import jsonutils

from tackerclient.i18n import _
from tackerclient.tacker import v1_0 as tackerV10

_VNFFGD = "vnffgd"


class ListVNFFGD(tackerV10.ListCommand):
    """List VNFFGDs that belong to a given tenant."""

    resource = _VNFFGD
    list_columns = ['id', 'name', 'template_source', 'description']

    def get_parser(self, prog_name):
        parser = super(ListVNFFGD, self).get_parser(prog_name)
        parser.add_argument(
            '--template-source',
            help=_("List VNFFGD with specified template source. Available \
                   options are 'onboarded' (default), 'inline' or 'all'"),
            action='store',
            default='onboarded')
        return parser

    def args2search_opts(self, parsed_args):
        search_opts = super(ListVNFFGD, self).args2search_opts(parsed_args)
        template_source = parsed_args.template_source
        if parsed_args.template_source:
            search_opts.update({'template_source': template_source})
        return search_opts


class ShowVNFFGD(tackerV10.ShowCommand):
    """Show information of a given VNFFGD."""

    resource = _VNFFGD


class CreateVNFFGD(tackerV10.CreateCommand):
    """Create a VNFFGD."""
    resource = _VNFFGD
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        parser.add_argument('--vnffgd-file', help=_('Specify VNFFGD file'))
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the VNFFGD'))
        parser.add_argument(
            '--description',
            help=_('Set a description for the VNFFGD'))

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        if parsed_args.vnffgd_file:
            with open(parsed_args.vnffgd_file) as f:
                vnffgd = yaml.safe_load(f.read())
                body[self.resource]['template'] = {'vnffgd': vnffgd}
        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description'])
        return body


class DeleteVNFFGD(tackerV10.DeleteCommand):
    """Delete a given VNFFGD."""
    resource = _VNFFGD


class ShowTemplateVNFFGD(tackerV10.ShowCommand):
    """Show template of a given VNFFGD."""
    resource = _VNFFGD

    def run(self, parsed_args):
        self.log.debug('run(%s)', parsed_args)
        template = None
        data = self.get_data(parsed_args)
        try:
            attributes_index = data[0].index('template')
            attributes_json = data[1][attributes_index]
            template = jsonutils.loads(attributes_json).get('vnffgd', None)
        except (IndexError, TypeError, ValueError) as e:
            self.log.debug('Data handling error: %s', str(e))
        print(template or _('Unable to display VNFFGD template!'))
