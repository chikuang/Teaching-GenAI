"""Python configuration for the Teaching-GenAI course book."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "_ext"))

project = "STAT XXXX Generative AI"
author = "Chi-Kuang Yeh"
copyright_year = "2026"
copyright = f"{copyright_year}, {author}"
extensions = ["myst_nb", "sphinx_copybutton", "sphinx_design", "code_folding", "chapter_equations"]
exclude_patterns = ["_build", "notebooks"]
master_doc = "index"
language = "en"
myst_enable_extensions = ["dollarmath", "amsmath", "colon_fence", "deflist"]
myst_heading_anchors = 4
nb_execution_mode = "cache"
nb_execution_timeout = 120
nb_execution_raise_on_error = True
nb_execution_show_tb = True
nb_execution_in_temp = True
html_theme = "sphinx_book_theme"
html_title = project
html_static_path = ["_static"]
html_css_files = ["course.css"]
html_js_files = ["learning-controls.js"]
templates_path = ["_templates"]
html_baseurl = "https://chikuang.github.io/teaching/genai/"
html_context = {
    "default_mode": "auto",
    "course_pdf": "STAT-XXXX-Generative-AI.pdf",
    "copyright_year": copyright_year,
    "author_url": "https://chikuang.github.io/",
}
html_theme_options = {
    # The book theme has its own header; avoid duplicate mobile toggle buttons.
    "navbar_persistent": [],
    "article_header_end": ["course-pdf-button.html", "article-header-buttons.html"],
    "pygments_light_style": "friendly",
    "pygments_dark_style": "monokai",
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
    "logo": {"text": "STAT XXXX Generative AI"},
    "footer_content_items": ["copyright.html", "last-updated.html", "extra-footer.html"],
    "extra_footer": "STAT XXXX Generative AI",
}
html_show_sourcelink = True
html_show_sphinx = False
html_last_updated_fmt = "%B %d, %Y"
numfig = True
# The chapter_equations extension gives labeled equations chapter-local numbers.
math_numfig = True
math_number_all = False
numfig_secnum_depth = 0
pygments_style = "friendly"
html_copy_source = True

# The same chapter tree and executed examples form the downloadable course book.
latex_engine = "xelatex"
latex_documents = [("index", "STAT-XXXX-Generative-AI.tex", project, author, "manual", True)]
latex_show_urls = "footnote"
latex_show_pagerefs = True
latex_domain_indices = False
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "11pt",
    "extraclassoptions": "oneside,openany",
    "geometry": r"\usepackage[margin=1in,headheight=26pt]{geometry}",
    "fncychap": "",
    "makeindex": "",
    "printindex": "",
    "tableofcontents": r"\renewcommand{\contentsname}{Contents}\tableofcontents",
    "sphinxsetup": r"VerbatimColor={RGB}{247,248,250},VerbatimBorderColor={RGB}{220,225,230},TitleColor={RGB}{48,56,66},InnerLinkColor={RGB}{162,0,110},OuterLinkColor={RGB}{162,0,110}",
    "preamble": r"""
\setcounter{secnumdepth}{-1}
\setcounter{tocdepth}{1}
% Keep internal equation anchors unique; chapter_equations sets printed numbers.
\counterwithout{equation}{chapter}
\fvset{fontsize=\small}
\setlength{\emergencystretch}{3em}
% Long appendix section names collide with page numbers in Sphinx's default footer.
\fancypagestyle{normal}{
  \fancyhf{}
  \fancyhead[R]{\small\sffamily STAT XXXX Generative AI}
  \fancyfoot[L]{\small\sffamily Teaching GenAI}
  \fancyfoot[R]{\small\sffamily\thepage}
  \renewcommand{\headrulewidth}{0.4pt}
  \renewcommand{\footrulewidth}{0.4pt}
}
""",
}
