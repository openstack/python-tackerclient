..
      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

=============
Command List
=============

The following list covers the extended commands for Tacker services
available in **openstack** command.

These commands can be referenced by doing **openstack help** and the detail
of individual command can be referred by **openstack help <command-name>**.

.. code-block:: console

  [legacy]
   openstack vim list                              List VIM(s) that belong to a given tenant.
   openstack vim register                          Create a VIM.
   openstack vim show                              Show information of a given VIM.
   openstack vim set                               Update a given VIM.
   openstack vim delete                            Delete given VIM(s).

  [v1] --os-tacker-api-version 1
   openstack vnf package create                    Create a new individual VNF package resource.
   openstack vnf package delete                    Delete given VNF package(s).
   openstack vnf package list                      List all VNF packages.
   openstack vnf package show                      Show package details.
   openstack vnf package upload                    Upload a VNF package.
   openstack vnf package download                  Download a VNF package.
   openstack vnf package artifact download         Download a VNF package artifact.
   openstack vnf package update                    Update a state of a VNF package.
   openstack vnflcm create                         Create a new VNF instance resource.
   openstack vnflcm instantiate                    Instantiate a VNF instance.
   openstack vnflcm list                           List VNF instance.
   openstack vnflcm show                           Show VNF instance.
   openstack vnflcm terminate                      Terminate a VNF instance.
   openstack vnflcm delete                         Delete a VNF instance resource.
   openstack vnflcm heal                           Heal a VNF instance.
   openstack vnflcm update                         Update information of a VNF instance.
   openstack vnflcm scale                          Scale a VNF instance.
   openstack vnflcm change-ext-conn                Change external VNF connectivity.
   openstack vnflcm op rollback                    Rollback a VNF LCM operation occurrence.
   openstack vnflcm op retry                       Retry a VNF LCM operation occurrence.
   openstack vnflcm op fail                        Fail a VNF LCM operation occurrence.
   openstack vnflcm op list                        List VNF LCM operation occurrence.
   openstack vnflcm op show                        Show VNF LCM operation occurrence.
   openstack vnflcm op cancel                      Cancel a VNF LCM operation occurrence.
   openstack vnflcm versions                       Show VNF LCM API versions.
   openstack vnflcm subsc create                   Create new subscription.
   openstack vnflcm subsc delete                   Delete subscription.
   openstack vnflcm subsc list                     List subscription.
   openstack vnflcm subsc show                     Show subscription.

  [v2] --os-tacker-api-version 2
   openstack vnflcm create                         Create a new VNF instance resource.
   openstack vnflcm instantiate                    Instantiate a VNF instance.
   openstack vnflcm list                           List VNF instance.
   openstack vnflcm show                           Show VNF instance.
   openstack vnflcm terminate                      Terminate a VNF instance.
   openstack vnflcm delete                         Delete a VNF instance resource.
   openstack vnflcm heal                           Heal a VNF instance.
   openstack vnflcm update                         Update information of a VNF instance.
   openstack vnflcm scale                          Scale a VNF instance.
   openstack vnflcm change-ext-conn                Change external VNF connectivity.
   openstack vnflcm change-vnfpkg                  Change current VNF package.
   openstack vnflcm op rollback                    Rollback a VNF LCM operation occurrence.
   openstack vnflcm op retry                       Retry a VNF LCM operation occurrence.
   openstack vnflcm op fail                        Fail a VNF LCM operation occurrence.
   openstack vnflcm op list                        List VNF LCM operation occurrence.
   openstack vnflcm op show                        Show VNF LCM operation occurrence.
   openstack vnflcm versions                       Show VNF LCM API versions.
   openstack vnflcm subsc create                   Create new subscription.
   openstack vnflcm subsc delete                   Delete subscription.
   openstack vnflcm subsc list                     List subscription.
   openstack vnflcm subsc show                     Show subscription.
   openstack vnffm alarm list                      List alarm.
   openstack vnffm alarm show                      Show alarm.
   openstack vnffm alarm update                    Update alarm.
   openstack vnffm sub create                      Create FM subscription.
   openstack vnffm sub list                        List FM subscription.
   openstack vnffm sub show                        Show FM subscription.
   openstack vnffm sub delete                      Delete FM subscription.
   openstack vnfpm job create                      Create PM job.
   openstack vnfpm job list                        List PM job.
   openstack vnfpm job show                        Show PM job.
   openstack vnfpm job update                      Update PM job.
   openstack vnfpm job delete                      Delete PM job.
   openstack vnfpm report show                     Show PM report.
   openstack vnfpm threshold create                Create PM threshold.
   openstack vnfpm threshold list                  List PM threshold.
   openstack vnfpm threshold show                  Show PM threshold.
   openstack vnfpm threshold update                Update PM threshold.
   openstack vnfpm threshold delete                Delete PM threshold.
