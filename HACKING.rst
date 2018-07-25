Tacker Style Commandments
=========================

- Step 1: Read the OpenStack Style Commandments
  https://docs.openstack.org/hacking/latest
- Step 2: Read on


Running Tests
-------------
The testing system is based on a combination of tox and stestr. The canonical
approach to running tests is to simply run the command ``tox``. This will
create virtual environments, populate them with dependencies and run all of
the tests that OpenStack CI systems run. Behind the scenes, tox is running
``stestr run``, but is set up such that you can supply any additional
stestr arguments that are needed to tox. For example, you can run:
``tox -- --analyze-isolation`` to cause tox to tell stestr to add
--analyze-isolation to its argument list.

It is also possible to run the tests inside of a virtual environment
you have created, or it is possible that you have all of the dependencies
installed locally already. In this case, you can interact with the stestr
command directly. Running ``stestr run`` will run the entire test suite.
``stestr run --concurrency=1`` will run tests serially (by default, stestr runs
tests in parallel). More information about stestr can be found at:
http://stestr.readthedocs.io/
