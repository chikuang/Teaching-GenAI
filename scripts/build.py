"""Execute the teaching notebooks and build the entire website with Python."""
from pathlib import Path
import os
import re
import shutil
import sys
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BUILD = ROOT / "_build"
OUTPUT = BUILD / "html"


def main():
    # Keep runtime files local and use the interpreter running this script.
    os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    for variable, folder in [("MPLCONFIGDIR", "matplotlib"), ("JUPYTER_RUNTIME_DIR", "jupyter")]:
        path = BUILD / folder
        path.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault(variable, str(path))
    from sphinx.cmd.build import build_main
    from myst_nb.core.read import read_myst_markdown_notebook
    import nbformat

    # A fresh output directory prevents removed chapters/assets from being published.
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    # Materialize notebook downloads before Sphinx checks local links.
    sources = []
    for path in sorted(DOCS.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        if content.startswith("---\n") and "file_format: mystnb" in content.split("---", 2)[1]:
            sources.append(path)
    downloads = DOCS / "notebooks"
    downloads.mkdir(exist_ok=True)
    for source in sources:
        notebook = read_myst_markdown_notebook(source.read_text(encoding="utf-8"), path=source)
        nbformat.validate(notebook)
        nbformat.write(notebook, downloads / (source.stem + ".ipynb"))

    status = build_main(["-b", "html", "-d", str(BUILD / "doctrees"),
                         "-E", "-a", "-W", "--keep-going", str(DOCS), str(OUTPUT)])
    if status:
        raise SystemExit(status)

    # MyST-NB stores executed notebooks here. Ship the same executed cells users see.
    executed = BUILD / "jupyter_execute"
    for source in sources:
        relative = source.relative_to(DOCS).with_suffix(".ipynb")
        candidate = executed / relative
        target = downloads / relative.name
        if not candidate.is_file():
            raise RuntimeError(f"Executed notebook missing: {candidate}")
        notebook = nbformat.read(candidate, as_version=4)
        code = [c for c in notebook.cells if c.cell_type == "code"]
        if not code or any(c.execution_count is None for c in code):
            raise RuntimeError(f"Unexecuted code cells: {candidate}")
        if any(o.output_type == "error" for c in code for o in c.outputs):
            raise RuntimeError(f"Notebook contains an error: {candidate}")
        # Keep navigation useful when a notebook is saved outside the source tree.
        page_url = "https://chikuang.github.io/teaching/genai/" + source.relative_to(DOCS).with_suffix(".html").as_posix()
        def public_link(match):
            opening, href, closing = match.groups()
            if not urlsplit(href).scheme and not href.startswith("#"):
                href = urljoin(page_url, re.sub(r"\.md(?=#|$)", ".html", href))
            return opening + href + closing
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                cell.source = re.sub(r'(\]\(|href=")([^"\s)]+)(\)|")', public_link, cell.source)
        nbformat.write(notebook, target)
    shutil.copytree(downloads, OUTPUT / "notebooks", dirs_exist_ok=True)
    (OUTPUT / ".nojekyll").touch()
    print(f"\nBuilt and executed with Python: {OUTPUT}")


if __name__ == "__main__":
    main()
