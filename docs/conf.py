# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

project = 'Biolink Model Toolkit'
copyright = '2022, Sierra Moxon; Deepak Unni'
author = 'Sierra Moxon; Deepak Unni'
release = '0.8.12'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
   'sphinx.ext.autodoc',
   'sphinx.ext.githubpages',
   'sphinx_rtd_theme',
   'recommonmark'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_context = {
    # "github_url": "https://github.com", # or your GitHub Enterprise interprise
    "github_user": "bmt",
    "github_repo": "biolink-model-toolkit",
    "github_version": "master/docs/",
    "display_github": True,  # Add 'Edit on Github' link instead of 'View page source'
    "conf_py_path": "/master/docs/", # Path in the checkout to the docs root
}