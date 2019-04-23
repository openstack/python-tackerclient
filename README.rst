========================
Team and repository tags
========================

.. image:: https://governance.openstack.org/tc/badges/python-tackerclient.svg
    :target: https://governance.openstack.org/tc/reference/tags/index.html

.. Change things from this point on

NFV Orchestration (Tacker) Client
=================================

CLI and Client Library for OpenStack Tacker

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
--------------------
Clone python-tackerclient repository.

  ::

    $ cd ~/
    $ git clone https://github.com/openstack/python-tackerclient -b <branch_name>


Install python-tackerclient.

  ::

    $ cd python-tackerclient
    $ sudo python setup.py install


Using pip
---------

You can also install the latest version by using ``pip`` command:

  ::

    $ pip install python-tackerclient


Or, if it is needed to install ``python-tackerclient`` from master branch,
type

  ::

    $ pip install git+https://github.com/openstack/python-tackerclient.git


More Information
================

* Python-tackerclient documentation: https://docs.openstack.org/python-tackerclient/latest/
* Tacker Documentation: https://docs.openstack.org/tacker/latest/
* Tacker Wiki: https://wiki.openstack.org/wiki/Tacker
* Release Notes: https://docs.openstack.org/releasenotes/python-tackerclient
