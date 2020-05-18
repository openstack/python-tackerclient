# -*- coding: utf-8 -*-
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

# python-tackerclient documentation build configuration file

import os
import sys

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#    sys.path.append(os.path.abspath('.'))

sys.path.insert(0, os.path.abspath('../..'))

# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc',
    'reno.sphinxext',
    'openstackdocstheme',
    'cliff.sphinxext',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
copyright = 'OpenStack Contributors'

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'native'

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'openstackdocs'

# Output file base name for HTML help builder.
htmlhelp_basename = 'tackerclientdoc'

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.

# -- Options for manual page output -------------------------------------------

man_pages = [
    ('cli/index', 'tacker', u'Client for Tacker API',
     [u'OpenStack Contributors'], 1),
]

# -- Options for openstackdocstheme -------------------------------------------

openstackdocs_repo_name = 'openstack/python-tackerclient'
openstackdocs_bug_project = 'python-tackerclient'
openstackdocs_bug_tag = 'doc'

# -- Options for cliff.sphinxext plugin ---------------------------------------

autoprogram_cliff_application = 'openstack'
