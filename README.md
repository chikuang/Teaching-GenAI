# Teaching-GenAI

**Topic Course · Generative AI through the lens of statisticians**  
Chi-Kuang Yeh · Independent study · Python

- [Course website](https://chikuang.github.io/teaching/genai/)
- [Complete Chapter 1](https://chikuang.github.io/teaching/genai/chapters/01-probability-to-genai.html)
- [14-chapter outline](https://chikuang.github.io/teaching/genai/syllabus.html)
- [Python setup and authoring guide](https://chikuang.github.io/teaching/genai/python-workflow.html)
- [Executed Chapter 1 notebook](https://chikuang.github.io/teaching/genai/notebooks/01-probability-to-genai.ipynb)

A self-paced course for a statistician with a PhD-level background in statistical
machine learning who is beginning to learn Python, attention, generative models,
and agents. Chapter 1 is a complete lesson with step-by-step code, mathematical
derivations, executed figures, eight exercises, and worked solutions. Chapters
2–14 have individual outline pages; their full lessons are planned work.

## Python builds the whole website

The site uses **Sphinx + MyST-NB + sphinx-book-theme**, with Waterloo black/yellow
and Faculty of Mathematics pink accents. `docs/` contains the canonical sources;
Python cells are executed during rendering. Quarto and Node.js are not required
to build the site. The earlier Quarto version is preserved in Git history.

Use Python 3.12. On macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build.py
python -m http.server 8767 --directory _build/html
```

Open `http://localhost:8767`. Windows users can create the environment with
`py -3.12 -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1`.
`requirements-lock.txt` records the tested macOS/Python 3.12 environment and may
need platform-specific adjustment elsewhere.

The build fails on notebook errors or Sphinx warnings and writes `_build/html/`.
Executed notebooks are exported to its `notebooks/` directory. The first chapter
requires no GPU, API key, or model download. To experiment locally, open a
downloaded notebook with `python -m jupyterlab`.

## Authoring

- `docs/chapters/*.md`: lessons, with MyST notebook metadata for executable pages.
- `docs/index.md`: homepage and chapter navigation.
- `docs/conf.py`: Python site configuration.
- `docs/_static/waterloo.css`: course styling.
- `scripts/build.py`: execute, render, validate notebook outputs, and export.

New executable MyST lessons are discovered automatically by the build script.
Add their paths to the homepage's toctree to include them in the sidebar.

## Publication

The public website is maintained in `chikuang/chikuang.github.io` on `master`.
After a successful build and preview, copy the **contents** of `_build/html/`
into that checkout's `teaching/genai/`, review the changes, and commit/push both
the course source and published output. Do not replace other website directories.
The Teaching entry is maintained in `chikuang/website`.

The GitHub Actions workflow validates the HTML build and saves a build artifact;
it does not publish automatically into the separate website repository.
