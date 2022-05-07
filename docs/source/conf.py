# flake8: noqa
# Configuration file for the Sphinx documentation builder.

import marsh

# -- Project information -----------------------------------------------------

project = 'Marsh'
copyright = '2022, Adrian Sahlman'
author = 'Adrian Sahlman'

# The full version, including alpha/beta/rc tags
release = marsh.__version__
version = release


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
]

add_module_names = False

# autodoc options
autodoc_inherit_docstrings = True
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'

# Add any paths that contain templates here, relative to this directory.
templates_path: list = []

intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

# The suffix(es) of source filenames.
source_suffix = '.rst'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns: list = []

# https://github.com/readthedocs/readthedocs.org/issues/2569
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'


html_context = {
  'display_github': True,
  'github_user': 'adriansahlman',
  'github_repo': 'marsh',
}


html_static_path = ['_static']


html_css_files = [
    'css/custom.css',
]
