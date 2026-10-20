# Teaching-GenAI

**Topic Course · Generative AI through the lens of statisticians**  
Chi-Kuang Yeh · Independent study · Python

- [Course website](https://chikuang.github.io/teaching/genai/)
- [Course outline](https://chikuang.github.io/teaching/genai/syllabus.html)
- [Python authoring guide](https://chikuang.github.io/teaching/genai/python-workflow.html)
- [First executable Python lab](https://chikuang.github.io/teaching/genai/01-python-lab.html)

A self-paced course for a statistician with a PhD-level background in statistical
machine learning who is beginning to learn attention, transformers, generative
models, and agents. The initial release contains a 14-module outline, a
statistical translation guide, selected readings, a Python publishing guide,
and one executable introductory lab. Full module lectures are planned work.

## Structure

This is a Quarto book, matching the structure of the existing statistics
courses, with a navy-and-amber theme. Python runs through Jupyter. The `.qmd`
files are canonical sources; `notebooks/01-python-lab.ipynb` is an exported
practice copy of the first lab.

## Local development

Install Python 3.12 and Quarto (initial build: Quarto 1.10.18).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export QUARTO_PYTHON="$PWD/.venv/bin/python"
quarto check jupyter
quarto preview
```

Windows: use `py -m venv .venv` and `.venv\Scripts\Activate.ps1`; set
`$env:QUARTO_PYTHON = "$PWD\.venv\Scripts\python.exe"` in PowerShell if needed.
The requirements lock records the initial macOS/Python 3.12 environment and may
need platform-specific adjustment on other operating systems.

## Build and refresh the notebook

```bash
quarto convert 01-python-lab.qmd --output notebooks/01-python-lab.ipynb
quarto render
```

The build executes Python cells and writes the website to `_book/`.
The course requires no R packages, API key, GPU, or model download for this lab.
PyTorch and model-specific dependencies will be introduced with later labs.

## Publication

The public website is maintained in `chikuang/chikuang.github.io` on `master`.
After a successful render and preview, copy the **contents** of `_book/` into
that checkout's `teaching/genai/`, review the changes, and commit/push both the
course source and the published output. Do not replace the website repository
or other teaching directories. The Teaching entry is maintained in
`chikuang/website` (`config.toml` and its teaching section partial).

The course repository's build workflow validates the HTML and saves a build
artifact; it does not automatically publish into the separate website repository.
