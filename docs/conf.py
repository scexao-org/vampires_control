from datetime import date

from pkg_resources import DistributionNotFound, get_distribution

# -- Project information -----------------------------------------------------
try:
    __version__ = get_distribution("vampires_control").version
except DistributionNotFound:
    __version__ = "unknown version"

# The full version, including alpha/beta/rc tags
version = __version__
release = __version__

project = "vampires_control"
author = "Miles Lucas"
# get current year
current_year = date.today().year
years = range(2022, current_year + 1)
copyright = f"{', '.join(map(str, years))}, {author}"


# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "myst_parser",
]
myst_enable_extensions = [
    "dollarmath",
]
myst_heading_anchors = 2

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autodoc_typehints = "description"
autodoc_typehints_format = "short"

# -- Options for HTML output -------------------------------------------------

# html_static_path = ["_static"]
html_title = "VAMPIRES Control"
html_theme = "sphinx_rtd_theme"
