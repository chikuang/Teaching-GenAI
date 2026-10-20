"""Python configuration for the Teaching-GenAI course book."""
project = "STAT XXXX Generate AI"
author = "Chi-Kuang Yeh"
copyright = "2026, Chi-Kuang Yeh"
extensions = ["myst_nb", "sphinx_copybutton", "sphinx_design"]
exclude_patterns = ["_build", "notebooks"]
master_doc = "index"
language = "en"
myst_enable_extensions = ["dollarmath", "amsmath", "colon_fence", "deflist"]
myst_heading_anchors = 4
nb_execution_mode = "force"
nb_execution_timeout = 120
nb_execution_raise_on_error = True
nb_execution_show_tb = True
nb_execution_in_temp = True
html_theme = "sphinx_book_theme"
html_title = project
html_static_path = ["_static"]
html_css_files = ["course.css"]
templates_path = ["_templates"]
html_baseurl = "https://chikuang.github.io/teaching/genai/"
html_context = {"default_mode": "light"}
html_theme_options = {
    # The book theme has its own header; avoid duplicate mobile toggle buttons.
    "navbar_persistent": [],
    "pygments_light_style": "friendly",
    "pygments_dark_style": "friendly",
    "repository_url": "https://github.com/chikuang/Teaching-GenAI",
    "repository_branch": "main",
    "path_to_docs": "docs",
    "use_repository_button": True,
    "use_source_button": True,
    "use_download_button": False,
    "show_navbar_depth": 1,
    "show_toc_level": 2,
    "navigation_depth": 3,
    "home_page_in_toc": True,
    "logo": {"text": "STAT XXXX Generate AI"},
    "extra_footer": "STAT XXXX Generate AI · Independent study",
}
html_show_sourcelink = True
html_show_sphinx = False
html_last_updated_fmt = "%B %d, %Y"
numfig = True
pygments_style = "friendly"
html_copy_source = True
