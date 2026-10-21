"""Execute the teaching notebooks and build the entire website with Python."""
from pathlib import Path
import argparse
import os
import re
import shutil
import sys
import subprocess
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BUILD = ROOT / "_build"
OUTPUT = BUILD / "html"
PDF_NAME = "STAT-XXXX-Generate-AI"


def main():
    parser = argparse.ArgumentParser(description="Build the course website and downloadable PDF.")
    parser.add_argument("--format", choices=["all", "pdf"], default="all",
                        help="Build both formats (default), or PDF only.")
    args = parser.parse_args()
    make_pdf = args.format in {"all", "pdf"}
    make_html = args.format == "all"
    if make_pdf:
        missing = [tool for tool in ("xelatex", "latexmk") if shutil.which(tool) is None]
        if missing:
            raise SystemExit("PDF build requires " + ", ".join(missing)
                             + ". Install TeX Live/MacTeX and make both commands available on PATH.")
    # Keep runtime files local and use the interpreter running this script.
    os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    for variable, folder in [("MPLCONFIGDIR", "matplotlib"), ("JUPYTER_RUNTIME_DIR", "jupyter")]:
        path = BUILD / folder
        path.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault(variable, str(path))
    from sphinx.cmd.build import build_main
    from myst_nb.core.read import read_myst_markdown_notebook
    import nbformat
    from jupyter_cache import get_cache

    # A fresh output directory prevents removed chapters/assets from being published.
    if make_html and OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True, exist_ok=True)

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

    def render(builder, destination):
        status = build_main(["-b", builder, "-d", str(BUILD / "doctrees"),
                             "-E", "-a", "-W", "--keep-going", str(DOCS), str(destination)])
        if status:
            raise SystemExit(status)

    if make_pdf:
        latex_output = BUILD / "latex"
        render("latex", latex_output)
        subprocess.run(["latexmk", "-xelatex", "-interaction=nonstopmode",
                        "-halt-on-error", "-file-line-error", "-no-shell-escape",
                        PDF_NAME + ".tex"], cwd=latex_output, check=True)
        pdf = latex_output / (PDF_NAME + ".pdf")
        if not pdf.is_file() or not pdf.read_bytes().startswith(b"%PDF-"):
            raise RuntimeError("The PDF build did not produce a valid PDF file.")
        shutil.copy2(pdf, OUTPUT / pdf.name)

    if make_html:
        # MyST-NB reuses identical executed cells for the web and PDF editions.
        render("html", OUTPUT)

    # Merge the same cached outputs used by both builders into fresh source text.
    # MyST-NB's jupyter_execute copy can lack outputs on a cache hit.
    cache = get_cache(str(BUILD / ".jupyter_cache"))
    for source in sources:
        relative = source.relative_to(DOCS).with_suffix(".ipynb")
        target = downloads / relative.name
        source_notebook = read_myst_markdown_notebook(source.read_text(encoding="utf-8"), path=source)
        _, notebook = cache.merge_match_into_notebook(source_notebook)
        nbformat.validate(notebook)
        code = [c for c in notebook.cells if c.cell_type == "code"]
        if not code or any(c.execution_count is None for c in code):
            raise RuntimeError(f"Unexecuted code cells: {source}")
        if any(o.output_type == "error" for c in code for o in c.outputs):
            raise RuntimeError(f"Notebook contains an error: {source}")
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
    print(f"\nBuilt course output: {OUTPUT}")
    if make_pdf:
        print(f"Course PDF: {OUTPUT / (PDF_NAME + '.pdf')}")


if __name__ == "__main__":
    main()
