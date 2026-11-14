###############
# Qiyas Sadıqov CC
###############

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

PACKAGE = "lalafo_sdk"
DIST = "lalafo-python-sdk"
TITLE = "lalafo Python SDK"
REPO = "https://github.com/qiyascc/lalafo-python-sdk"
SITE = "https://theqiyas.cc"
PROJECT_PAGE = "https://theqiyas.cc/projects/lalafo-sdk/"

from lalafo_sdk import __version__ as release

project = TITLE
author = "Qiyas Sadıqov"
copyright = f"{date.today().year}, Qiyas Sadıqov"
version = release

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
]

source_suffix = {".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build"]
language = "en"

myst_enable_extensions = ["colon_fence", "deflist", "fieldlist", "attrs_inline", "attrs_block", "substitution"]
myst_heading_anchors = 3
myst_substitutions = {"dist": DIST, "package": PACKAGE, "version": release}

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {"members": True, "undoc-members": True}
nitpick_ignore_regex = [(r"py:.*", rf"(?!{PACKAGE}\.).*")]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
intersphinx_disabled_reftypes = ["*"]

copybutton_prompt_text = r"\$ |>>> |\.\.\. "
copybutton_prompt_is_regexp = True

html_theme = "furo"
html_title = TITLE
html_static_path = ["_static"]
html_templates_path = ["_templates"]
templates_path = ["_templates"]
html_css_files = ["qiyas.css"]
html_show_sphinx = False
html_last_updated_fmt = "%Y-%m-%d"
html_context = {"site_url": SITE, "project_page": PROJECT_PAGE, "repo_url": REPO, "dist": DIST}
html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/author.html",
        "sidebar/scroll-end.html",
    ]
}

GITHUB = """<svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path></svg>"""
GLOBE = """<svg stroke="currentColor" fill="none" stroke-width="1.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"></circle><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"></path></svg>"""
PYPI = """<svg stroke="currentColor" fill="none" stroke-width="1.5" viewBox="0 0 24 24"><path d="M12 2 3 7v10l9 5 9-5V7l-9-5z"></path><path d="M3 7l9 5 9-5M12 12v10"></path></svg>"""

html_theme_options = {
    "source_repository": REPO,
    "source_branch": "main",
    "source_directory": "docs/",
    "light_css_variables": {
        "color-brand-primary": "#0f766e",
        "color-brand-content": "#0f766e",
    },
    "dark_css_variables": {
        "color-brand-primary": "#5eead4",
        "color-brand-content": "#5eead4",
    },
    "footer_icons": [
        {"name": "GitHub", "url": REPO, "html": GITHUB, "class": ""},
        {"name": "PyPI", "url": f"https://pypi.org/project/{DIST}/", "html": PYPI, "class": ""},
        {"name": "theqiyas.cc", "url": SITE, "html": GLOBE, "class": ""},
    ],
}
