# -*- coding: utf-8 -*-
#
# EasyFleet documentation build configuration file.
#
# This file is execfile()d with the current directory set to its
# containing dir.

import os
import sys
import time

sys.path.insert(0, os.path.abspath('.'))


# -- General configuration ------------------------------------------------

extensions = [
    'sphinx.ext.extlinks',
    'sphinx.ext.graphviz',
]

graphviz_output_format = 'png'
graphviz_dot_args = [
   '-Nfontname="verdana"',
   '-Gfontname="verdana"',
   '-Efontname="verdana"']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'EasyFleet'
author = u'Intelligent Robotics Lab, Universidad Rey Juan Carlos'
copyright = f'{time.strftime("%Y")}, {author}'

version = release = "1.0.0"

language = 'en'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', '_themes', 'scripts']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Options for HTML output ----------------------------------------------

try:
    import sphinx_rtd_theme
except ImportError:
    html_theme = 'alabaster'
    html_sidebars = {
        '**': [
            'relations.html',
            'searchbox.html',
            ]
        }
    sys.stderr.write('Warning: sphinx_rtd_theme missing. Use pip to install it.\n')
else:
    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
    html_theme_options = {
        'canonical_url': '',
        'analytics_id': '',
        'logo_only': False,
        'display_version': True,
        'prev_next_buttons_location': 'None',
        'style_nav_header_background': 'orange',
        # Toc options
        'collapse_navigation': False,
        'sticky_navigation': True,
        'navigation_depth': 4,
    }

html_theme_path = ['_themes']
html_theme = 'otc_tcs_sphinx_theme'

# Here's where we (manually) list the document versions maintained on
# the published doc website. On a daily basis we publish to the
# /latest folder but when releases are made, we publish to a /<relnum>
# folder (specified via RELEASE=name on the make command).

if tags.has('release'):
   current_version = version
else:
   version = current_version = "latest"

html_context = {
   'current_version': current_version,
   'versions': ( ("latest", "/latest/"),
               )
    }

html_logo = 'images/easyfleet_logo.png'
html_favicon = 'images/favicon.png'

numfig = True
numfig_format = {'figure': 'Figure %s', 'table': 'Table %s', 'code-block': 'Code Block %s'}

# If true, "Created using Sphinx" is shown in the HTML footer.
html_show_sphinx = False

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

html_last_updated_fmt = None

# -- Options for HTMLHelp output ------------------------------------------

rst_epilog = """
.. include:: /substitutions.txt
"""

extlinks = {'projectfile':
    ('https://github.com/EasyNavigation/EasyFleet/blob/rolling/%s', 'filepath ')}
