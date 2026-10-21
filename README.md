# STAT XXXX Generative AI

**Topic Course · Generative AI through the lens of statisticians**  
Chi-Kuang Yeh · Independent study · Python

- [Course website](https://chikuang.github.io/teaching/genai/)
- [Download course PDF](https://chikuang.github.io/teaching/genai/STAT-XXXX-Generative-AI.pdf)
- [Complete Chapter 1](https://chikuang.github.io/teaching/genai/chapters/01-probability-to-genai.html)
- [14-chapter course guide](https://chikuang.github.io/teaching/genai/syllabus.html)
- [Python setup and authoring guide](https://chikuang.github.io/teaching/genai/python-workflow.html)
- [Executed Chapter 1 notebook](https://chikuang.github.io/teaching/genai/notebooks/01-probability-to-genai.ipynb)

A self-paced course for a statistician with a PhD-level background in statistical
machine learning who is beginning to learn Python, attention, generative models,
and agents. All 14 chapters contain developed lessons, mathematical explanations,
executed Python experiments, exercises, worked solutions, and downloadable notebooks.
The core labs run on a CPU with NumPy and PyTorch, without API keys or downloaded
model weights. RAG and agent chapters include explicit offline baselines and
separately describe language-model integration extensions. The capstone implements
and evaluates a bounded statistical simulation assistant.

Every chapter includes a workflow or architecture diagram and a table of component
contracts and checks. The RAG chapter develops the indexing/query-time distinction,
retrieval alternatives, context packing, prompt construction, citation validation,
and controlled failure diagnosis in one executable example. Its extractive backend
is explicitly separate from a real language-model adapter.

Workflow diagrams use a restrained layout with small chibi memory icons,
readable labels, and a short recall cue. The illustrations were created with
the built-in image generation tool; `scripts/framework_art.json` records the
final prompts. The checked-in PNGs in `docs/_static/diagrams/` appear in HTML,
the PDF, and downloadable notebooks without a JavaScript diagram dependency.
`python scripts/draw_frameworks.py` renders plain reference drafts into
`_build/framework-drafts/` without overwriting the published illustrations.

## Build the website and course PDF

The site uses **Sphinx + MyST-NB + sphinx-book-theme**, with light, dark, and system-following themes,
readable system fonts, Waterloo yellow, and Mathematics pink accents. `docs/` contains the canonical sources;
Python cells are executed during rendering. Quarto and Node.js are not required
to build the site. The earlier Quarto version is preserved in Git history.

Use Python 3.12 and a TeX installation providing `xelatex` and `latexmk`.
MacTeX on macOS or TeX Live on Linux provides the PDF typesetting tools. On
Ubuntu, install `latexmk texlive-xetex texlive-latex-extra texlive-fonts-recommended fonts-freefont-otf`.

On macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build.py
python -m http.server 8767 --directory _build/html
```

Open `http://localhost:8767`. Windows users can create the environment with
`py -3.12 -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1`.
`requirements-lock.txt` records package versions from the tested macOS/Python 3.13
environment; CI also builds the course with Python 3.12 on Linux. Use
`requirements.txt` for portable installation. The Linux workflow installs CPU-only
PyTorch before the other dependencies to avoid unnecessary CUDA packages.

The default command builds both HTML and a typeset, complete course PDF from the
same chapter tree. MyST-NB caches successful notebook executions so both formats
use the same outputs; changed notebook content is executed again. The build fails
on notebook errors, Sphinx warnings, or a LaTeX compilation error and writes `_build/html/`.

The PDF is `_build/html/STAT-XXXX-Generative-AI.pdf`. It includes a linked contents
page, formulas, code, executed outputs, and figures. To regenerate only the PDF:

```bash
python scripts/build.py --format pdf
```

This also updates the PDF in `_build/html/`, ready to publish with the website.
The generated LaTeX and compile logs are under `_build/latex/`.
Executed notebooks are exported to its `notebooks/` directory. All core labs
require no GPU, API key, or model download. To experiment locally, open a
downloaded notebook with `python -m jupyterlab`.

## Authoring

- `docs/chapters/*.md`: lessons, with MyST notebook metadata for executable pages.
- `docs/index.md`: homepage and chapter navigation.
- `docs/conf.py`: Python site configuration.
- `docs/_static/course.css`: course styling.
- `scripts/build.py`: execute, render, validate notebook outputs, and export.

New executable MyST lessons are discovered automatically by the build script.
Add their paths to the homepage's toctree to include them in the sidebar.

HTML code blocks are folded by default. Click **Code** (or focus it and press
Enter/Space) to expand or collapse a block. `docs/_ext/code_folding.py` applies
this to executable inputs and ordinary fenced code throughout the course. Expanded
code has a light pink background; outputs and plots stay visible in a light yellow
panel labeled **Output**. Both colors adapt to dark mode. The PDF and downloaded
notebooks retain all code.

Give equations that are discussed later a descriptive MyST label on the closing
delimiter, such as `$$ (eq-attention)`, and refer to them using
`Equation {eq}` followed by the label in backticks. HTML and PDF number labeled
equations within each course chapter, such as `(10.1)` and `(10.2)` in Chapter 10;
leave one-off expressions unnumbered. Chapter numbers follow the numbered
`docs/chapters/` filenames, so course-guide pages do not shift the equation numbers.
The notebook exporter converts equation references to numbered links to the
course website and removes MyST label syntax from displayed math.

## Publication

The public website is maintained in `chikuang/chikuang.github.io` on `master`.
After a successful build and preview, copy the **contents** of `_build/html/`
into that checkout's `teaching/genai/`, review the changes, and commit/push both
the course source and published output. Do not replace other website directories.
The Teaching entry is maintained in `chikuang/website`.

The GitHub Actions workflow installs TeX, validates both HTML and PDF, and saves a build artifact;
it does not publish automatically into the separate website repository.
