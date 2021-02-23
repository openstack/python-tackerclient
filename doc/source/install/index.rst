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

============
Installation
============

This document describes how to install python-tackerclient.

.. note::

   This installation guide contents are specific to Ubuntu distro.

Using python install
====================

#. Clone python-tackerclient repository.

   You can use -b for specific release, optionally.

   .. code-block:: console

       $ cd ~/
       $ git clone https://opendev.org/openstack/python-tackerclient -b <branch_name>

   .. note::

      Make sure to replace the ``<branch_name>`` in command example with
      specific branch name, such as ``stable/victoria``.

#. Install python-tackerclient.

   .. code-block:: console

       $ cd python-tackerclient
       $ sudo python3 setup.py install

Using pip
=========

You can also install the latest version by using ``pip`` command:

.. code-block:: console

    $ pip3 install python-tackerclient

Or, if it is needed to install ``python-tackerclient`` from master branch,
type

.. code-block:: console

    $ pip3 install git+https://opendev.org/openstack/python-tackerclient

