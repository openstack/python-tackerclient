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

from tackerclient.tacker import v1_0 as tackerV10
import yaml

_CLUSTER = 'cluster'
_CLUSTER_MEMBER = 'clustermember'


class ListCluster(tackerV10.ListCommand):
    """List Clusters that belong to a given tenant."""

    resource = _CLUSTER
    list_columns = ['id', 'name', 'vnfd_id', 'status', 'vip_endpoint']


class ShowCluster(tackerV10.ShowCommand):
    """Show information of a given Cluster."""

    resource = _CLUSTER


class DeleteCluster(tackerV10.DeleteCommand):
    """Delete a given Cluster."""

    resource = _CLUSTER


class CreateCluster(tackerV10.CreateCommand):
    """Create a Cluster."""

    resource = _CLUSTER

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help='Set a name for the VNF cluster')
        vnfd_group = parser.add_mutually_exclusive_group(required=True)
        vnfd_group.add_argument(
            '--vnfd-id',
            help='VNFD ID to use as template to create member VNF')
        vnfd_group.add_argument(
            '--vnfd-name',
            help='VNFD name to use as template to create member VNF')
        parser.add_argument('--policy-file',
                            help='Specify policy file for cluster',
                            required=True)
        parser.add_argument(
            '--description',
            help='Set a description for the created VNF cluster')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        tacker_client = self.get_client()
        tacker_client.format = parsed_args.request_format

        if parsed_args.vnfd_name:
            _id = tackerV10.find_resourceid_by_name_or_id(tacker_client,
                                                          'vnfd',
                                                          parsed_args.
                                                          vnfd_name)
            parsed_args.vnfd_id = _id
        policy_info = None
        with open(parsed_args.policy_file) as f:
            policy_info = yaml.safe_load(f.read())
        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'vnfd_id', 'description'])
        if policy_info:
            body[self.resource]['policy_info'] = policy_info
        return body


class AddClusterMember(tackerV10.CreateCommand):
    """Add a new Cluster Member to given Cluster."""

    resource = _CLUSTER_MEMBER

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help='Set a name for the VNF cluster member')
        cluster_group = parser.add_mutually_exclusive_group()
        cluster_group.add_argument(
            '--cluster-id',
            help='VNFD ID to use as template to create member VNF')
        cluster_group.add_argument(
            '--cluster-name',
            help='VNFD name to use as template to create member VNF')
        vnfd_group = parser.add_mutually_exclusive_group()
        vnfd_group.add_argument(
            '--vnfd-id',
            help='Set a id for the VNFD')
        vnfd_group.add_argument(
            '--vnfd-name',
            help='Set a name for the VNFD')
        parser.add_argument(
            '--role',
            help='Set a [Active/Standby] role to cluster member',
            required=True)
        vim_group = parser.add_mutually_exclusive_group()
        vim_group.add_argument(
            '--vim-id',
            help='Set a VIM ID to deploy cluster member')
        vim_group.add_argument(
            '--vim-name',
            help='Set a VIM name to deploy cluster member')

    def args2body(self, parsed_args):
        body = {self.resource: {}}

        tacker_client = self.get_client()
        tacker_client.format = parsed_args.request_format
        if parsed_args.cluster_name:
            _id = tackerV10.find_resourceid_by_name_or_id(tacker_client,
                                                          'cluster',
                                                          parsed_args.
                                                          cluster_name)
            parsed_args.cluster_id = _id
        if parsed_args.vnfd_name:
            _id = tackerV10.find_resourceid_by_name_or_id(tacker_client,
                                                          'vnfd',
                                                          parsed_args.
                                                          vnfd_name)
            parsed_args.vnfd_id = _id
        parsed_args.role = parsed_args.role.upper()
        if parsed_args.vim_name:
            _id = tackerV10.find_resourceid_by_name_or_id(tacker_client,
                                                          'vim',
                                                          parsed_args.
                                                          vim_name)
            parsed_args.vim_id = _id
        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'cluster_id', 'vnfd_id',
                               'role', 'vim_id'])
        return body


class ListClusterMember(tackerV10.ListCommand):
    """List Cluster Members that belong to a given tenant."""

    resource = _CLUSTER_MEMBER

    def add_known_arguments(self, parser):
        cluster_group = parser.add_mutually_exclusive_group(required=True)
        cluster_group.add_argument(
            '--cluster-id',
            help='Set a ID for the queried cluster')
        cluster_group.add_argument(
            '--cluster-name',
            help='Set a name for the queried cluster')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        tacker_client = self.get_client()
        tacker_client.format = parsed_args.request_format

        if parsed_args.cluster_name:
            _id = tackerV10.find_resourceid_by_name_or_id(tacker_client,
                                                          'cluster',
                                                          parsed_args.
                                                          cluster_name)
            parsed_args.cluster_id = _id

        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'cluster_id'])
        return body

    list_columns = ['id', 'name', 'cluster_id', 'role', 'vnf_id',
                    'vim_id', 'mgmt_ip_address', 'lb_member_id']


class DeleteClusterMember(tackerV10.DeleteCommand):
    """Delete a given Cluster Member."""

    resource = _CLUSTER_MEMBER


class ShowClusterMember(tackerV10.ShowCommand):
    """Show information of a given Cluster Member."""

    resource = _CLUSTER_MEMBER
