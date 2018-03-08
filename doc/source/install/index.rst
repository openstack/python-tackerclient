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

      Convention for heading levels in Neutron devref:
      =======  Heading 0 (reserved for the title in a document)
      -------  Heading 1
      ~~~~~~~  Heading 2
      +++++++  Heading 3
      '''''''  Heading 4
      (Avoid deeper levels because they do not render well.)

============
Installation
============

**Note:** The paths we are using for configuration files in these steps
are with reference to Ubuntu Operating System. The paths may vary for
other Operating Systems.

The branch_name which is used in commands, specify the branch_name
as stable/<branch> for any stable branch installation. For eg:
stable/queens, stable/pike. If unspecified the default will be
master branch.

Using python install
====================
1. Clone python-tackerclient repository.

  ::

    $ cd ~/
    $ git clone https://github.com/openstack/python-tackerclient -b <branch_name>


2. Install python-tackerclient.

  ::

    $ cd python-tackerclient
    $ sudo python setup.py install


Using pip
=========

You can also install the latest version by using ``pip`` command:

  ::

    $ pip install python-tackerclient


Or, if it is needed to install ``python-tackerclient`` from master branch,
type

  ::

    $ pip install git+https://github.com/openstack/python-tackerclient.git

