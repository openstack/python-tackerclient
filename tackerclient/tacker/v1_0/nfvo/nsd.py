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

_NSD = "nsd"


class ListNSD(tackerV10.ListCommand):
    """List NSDs that belong to a given tenant."""

    resource = _NSD
    list_columns = ['id', 'name', 'template_source', 'description']

    def get_parser(self, prog_name):
        parser = super(ListNSD, self).get_parser(prog_name)
        parser.add_argument(
            '--template-source',
            help=_("List NSD with specified template source. Available \
                   options are 'onboared' (default), 'inline' or 'all'"),
            action='store',
            default='onboarded')
        return parser

    def args2search_opts(self, parsed_args):
        search_opts = super(ListNSD, self).args2search_opts(parsed_args)
        template_source = parsed_args.template_source
        if parsed_args.template_source:
            search_opts.update({'template_source': template_source})
        return search_opts


class ShowNSD(tackerV10.ShowCommand):
    """Show information of a given NSD."""

    resource = _NSD


class CreateNSD(tackerV10.CreateCommand):
    """Create a NSD."""
    resource = _NSD
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        parser.add_argument('--nsd-file', help='Specify NSD file',
                            required=True)
        parser.add_argument(
            'name', metavar='NAME',
            help='Set a name for the NSD')
        parser.add_argument(
            '--description',
            help='Set a description for the NSD')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        nsd = None
        with open(parsed_args.nsd_file) as f:
            nsd = yaml.safe_load(f.read())
        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description'])
        if nsd:
            body[self.resource]['attributes'] = {'nsd': nsd}

        return body


class DeleteNSD(tackerV10.DeleteCommand):
    """Delete a given NSD."""
    resource = _NSD


class ShowTemplateNSD(tackerV10.ShowCommand):
    """Show template of a given NSD."""
    resource = _NSD

    def run(self, parsed_args):
        self.log.debug('run(%s)', parsed_args)
        template = None
        data = self.get_data(parsed_args)
        try:
            attributes_index = data[0].index('attributes')
            attributes_json = data[1][attributes_index]
            template = jsonutils.loads(attributes_json).get('nsd', None)
        except (IndexError, TypeError, ValueError) as e:
            self.log.debug('Data handling error: %s', str(e))
        print(template or _('Unable to display NSD template!'))
