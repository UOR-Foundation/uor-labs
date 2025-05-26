import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'uor-labs'
extensions = ['sphinx.ext.autodoc']
exclude_patterns = ['_build']
html_theme = 'alabaster'
