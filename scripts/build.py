"""Execute the teaching notebooks and build the entire website with Python."""
from pathlib import Path
import argparse
import os
import pickle
import re
import shutil
import sys
import subprocess
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BUILD = ROOT / "_build"
OUTPUT = BUILD / "html"
PDF_NAME = "STAT-XXXX-Generative-AI"


def notebook_examples(markdown):
    """Render the course's MyST example boxes in ordinary Jupyter Markdown."""
    def blockquote(match):
        title, options, body = match.groups()
        if ":class: course-example" not in options.splitlines():
            return match[0]
        lines = [f"**{title}**", "", *body.strip().splitlines()]
        return "\n".join("> " + line if line else ">" for line in lines)

    markdown = re.sub(r"(?ms)^```\{tabularcolumns\}[^\n]*\n.*?^```[ \t]*\n?", "", markdown)
    # Print-only page breaks have no meaning in an ordinary Jupyter notebook.
    markdown = re.sub(r"(?ms)^```\{raw\} latex[ \t]*\n.*?^```[ \t]*\n?", "", markdown)
    # Jupyter understands HTML disclosure widgets, not Sphinx dropdown directives.
    markdown = re.sub(
        r"(?ms)^:::\{dropdown\} ([^\n]+)\n(?:\n|:[^\n]*\n)*(.*?)\n:::[ \t]*$",
        lambda m: "<details><summary>" + m[1] + "</summary>\n\n" + m[2].strip() + "\n\n</details>", markdown)
    return re.sub(
        r"(?ms)^:::\{admonition\} (Example [^\n]+)\n"
        r"((?::[^\n]*\n)+)\n(.*?)\n:::[ \t]*$",
        blockquote, markdown,
    )


def main():
    parser = argparse.ArgumentParser(description="Build the course website and downloadable PDF.")
    parser.add_argument("--format", choices=["all", "html", "pdf"], default="all",
                        help="Build both formats (default), HTML without TeX, or PDF only.")
    args = parser.parse_args()
    make_pdf = args.format in {"all", "pdf"}
    make_html = args.format in {"all", "html"}
    os.environ["GENAI_COURSE_ROOT"] = str(ROOT)
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
    # External experiment records are inputs to Appendix B: do not reuse stale outputs.
    experiment_cache = BUILD / ".jupyter_cache"
    record = DOCS / "_static" / "experiments" / "llm-run.json"
    if record.exists():
        import hashlib
        external_inputs = sorted(record.parent.glob("*.json")) + sorted((ROOT / "labs").glob("*.py"))
        digest = hashlib.sha256(b"".join(p.read_bytes() for p in external_inputs)).hexdigest()
        stamp = BUILD / "experiment.sha256"
        if not stamp.exists() or stamp.read_text() != digest:
            if experiment_cache.exists():
                shutil.rmtree(experiment_cache)
            BUILD.mkdir(exist_ok=True)
            stamp.write_text(digest)
    from sphinx.cmd.build import build_main
    from myst_nb.core.read import read_myst_markdown_notebook
    import nbformat
    from jupyter_cache import get_cache
    from docutils.nodes import make_id

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
                             "-E", "-a", "-W", "--keep-going",
                             "-A", f"course_has_pdf={int(make_pdf)}", str(DOCS), str(destination)])
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
        # Keep previously shared PDF links working after the title correction.
        shutil.copy2(pdf, OUTPUT / "STAT-XXXX-Generate-AI.pdf")

    if make_html:
        # MyST-NB reuses identical executed cells for the web and PDF editions.
        render("html", OUTPUT)

    # Merge the same cached outputs used by both builders into fresh source text.
    # MyST-NB's jupyter_execute copy can lack outputs on a cache hit.
    # This is the trusted environment just generated by our own Sphinx build.
    # Resolve MyST equation roles into ordinary links for Jupyter's Markdown renderer.
    with (BUILD / "doctrees" / "environment.pickle").open("rb") as handle:
        environment = pickle.load(handle)
    equation_links = {}
    for label, (docname, _) in environment.domaindata["math"]["objects"].items():
        anchor = make_id("equation-" + label)
        number = ".".join(map(str, environment.toc_fignumbers[docname]["displaymath"][anchor]))
        url = f"https://chikuang.github.io/teaching/genai/{docname}.html#{anchor}"
        equation_links[label] = f"[({number})]({url})"

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
                # MyST heading slugs differ from the actual HTML element IDs.
                parsed = urlsplit(href)
                prefix = "/teaching/genai/"
                docname = parsed.path.removeprefix(prefix).removesuffix(".html")
                slug = environment.metadata.get(docname, {}).get("myst_slugs", {}).get(parsed.fragment)
                if slug:
                    href = href.rsplit("#", 1)[0] + "#" + slug[1]
            return opening + href + closing
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                cell.source = re.sub(r'(\]\(|href=")([^"\s)]+)(\)|")', public_link, cell.source)
                cell.source = re.sub(r"\{eq\}`([^`]+)`",
                                     lambda match: equation_links[match[1]], cell.source)
                cell.source = re.sub(r"(?m)^\$\$ \(eq-[\w-]+\)$", "$$", cell.source)
                cell.source = notebook_examples(cell.source)
        nbformat.write(notebook, target)
    shutil.copytree(downloads, OUTPUT / "notebooks", dirs_exist_ok=True)
    # Live notebooks are downloadable artifacts, excluded from Sphinx source discovery.
    shutil.copytree(DOCS / "_static" / "live-notebooks",
                    OUTPUT / "_static" / "live-notebooks", dirs_exist_ok=True)
    (OUTPUT / ".nojekyll").touch()
    print(f"\nBuilt course output: {OUTPUT}")
    if make_pdf:
        print(f"Course PDF: {OUTPUT / (PDF_NAME + '.pdf')}")


if __name__ == "__main__":
    main()
