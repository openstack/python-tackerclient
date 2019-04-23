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

===================================
Developing with Python-TackerClient
===================================

Project Info
============

* **Free software:** under the `Apache license <http://www.apache.org/licenses/LICENSE-2.0>`_
* **Tacker Service:** https://opendev.org/openstack/tacker
* **Tacker Client Library:** https://opendev.org/openstack/python-tackerclient
* **Tacker Service Bugs:** https://bugs.launchpad.net/tacker
* **Client Bugs:** https://bugs.launchpad.net/python-tackerclient
* **Blueprints:** https://blueprints.launchpad.net/tacker

Meetings
========
For details please refer to the `OpenStack IRC meetings`_ page.

.. _`OpenStack IRC meetings`: http://eavesdrop.openstack.org/#Tacker_(NFV_Orchestrator_and_VNF_Manager)_Team_Meeting

Testing
=======

Install the prerequisites for Tox:

* On Ubuntu or Debian:

  .. code-block:: bash

    $ apt-get install gcc gettext python-dev libxml2-dev libxslt1-dev \
      zlib1g-dev

  You may need to use pip install for some packages.


* On RHEL or CentOS including Fedora:

  .. code-block:: bash

    $ yum install gcc python-devel libxml2-devel libxslt-devel

* On openSUSE or SUSE linux Enterprise:

  .. code-block:: bash

    $ zypper install gcc python-devel libxml2-devel libxslt-devel

Install python-tox:

.. code-block:: bash

    $ pip install tox

To run the full suite of tests maintained within TackerClient.

.. code-block:: bash

    $ tox

.. NOTE::

    The first time you run ``tox``, it will take additional time to build
    virtualenvs. You can later use the ``-r`` option with ``tox`` to rebuild
    your virtualenv in a similar manner.


To run tests for one or more specific test environments(for example, the
most common configuration of Python 2.7, Python 3.5 and PEP-8), list the
environments with the ``-e`` option, separated by spaces:

.. code-block:: bash

    $ tox -e py27,py35,pep8

See ``tox.ini`` for the full list of available test environments.

Building the Documentation
==========================

The documentation is generated with Sphinx using the ``tox`` command. To
create HTML docs, run the commands:

.. code-block:: bash

    $ tox -e docs

The resultant HTML will be in the ``doc/build/html`` directory.

Release Notes
=============

The release notes for a patch should be included in the patch.  See the
`Project Team Guide`_ for more information on using reno in OpenStack.

.. _`Project Team Guide`: http://docs.openstack.org/project-team-guide/release-management.html#managing-release-notes

If any of the following applies to the patch, a release note is required:

* The deployer needs to take an action when upgrading
* The plugin interface changes
* A new feature is implemented
* A command or option is removed
* Current behavior is changed
* A security bug is fixed

Reno is used to generate release notes. Use the commands:

.. code-block:: bash

    $ tox -e venv -- reno new <bug-,bp-,whatever>

Then edit the sample file that was created and push it with your change.

To run the commands and see results:

.. code-block:: bash

    $ git commit  # Commit the change because reno scans git log.

    $ tox -e releasenotes

At last, look at the generated release notes
files in ``releasenotes/build/html`` in your browser.

Testing new code
================

If a developer wants to test new code (feature, command or option) that
they have written, Python-TackerClient may be installed from source by running
the following commands in the base directory of the project:

.. code-block:: bash

   $ python setup.py install

or

.. code-block:: bash

   $ pip install -e .

Standardize Import Format
=========================

.. _`Import Order Guide`: https://docs.openstack.org/hacking/latest/user/hacking.html#imports

The import order shows below:

* {{stdlib imports in human alphabetical order}}
* \n
* {{third-party lib imports in human alphabetical order}}
* \n
* {{project imports in human alphabetical order}}
* \n
* \n
* {{begin your code}}

Example
~~~~~~~

.. code-block:: python

    import copy
    import fixtures
    import mock
    import os

    from osc_lib.api import auth
    from osc_lib import utils
    import six

    from openstackclient import shell
    from openstackclient.tests import utils

