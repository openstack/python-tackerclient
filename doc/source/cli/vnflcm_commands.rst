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

================
VNF Lcm commands
================

VNF LCM commands are CLI interface of VNF Lifecycle Management Interface in
`ETSI NFV-SOL 002 <https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/03.03.01_60/gs_NFV-SOL002v030301p.pdf>`_
and `ETSI NFV-SOL 003 <https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf>`_.

.. note::
    Commands call version 1 vnflcm APIs by default.
    You can call the specific version of vnflcm APIs
    by using the option **\-\-os-tacker-api-version**.
    Commands with **\-\-os-tacker-api-version 2** call version 2 vnflcm APIs.
    **vnflcm op cancel** is included in only version 1 vnflcm APIs
    and **change-vnfpkg** is included in only version 2 vnflcm APIs.

.. autoprogram-cliff:: openstack.tackerclient.v1
   :command: vnflcm *

.. autoprogram-cliff:: openstack.tackerclient.v2
   :command: vnflcm change-vnfpkg
