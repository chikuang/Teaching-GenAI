"""Number equations by course chapter without numbering the course-guide pages."""
import re

from docutils import nodes
from sphinx.writers.latex import LaTeXTranslator


def number_chapter_equations(app, env):
    """Replace the default figure sequence after Sphinx collects figure numbers."""
    changed = False
    for docname, figures in env.toc_fignumbers.items():
        chapter = re.fullmatch(r"chapters/(\d+)-[^/]+", docname)
        if chapter is None or "displaymath" not in figures:
            continue
        numbers = {
            anchor: (int(chapter[1]), index)
            for index, anchor in enumerate(figures["displaymath"], start=1)
        }
        changed |= figures["displaymath"] != numbers
        figures["displaymath"] = numbers
    # References can also occur in the course guide or a different chapter.
    return sorted(env.found_docs) if changed else []


def visit_latex_equation(translator, node):
    if node.get("label"):
        numbers = translator.builder.env.toc_fignumbers[node["docname"]]["displaymath"]
        printed = ".".join(map(str, numbers[node["ids"][0]]))
        # Keep LaTeX's internal counter increasing for unique PDF anchors.
        # Change only the printed number, with no extra paragraph or spacing.
        translator.body.append(rf"\renewcommand{{\theequation}}{{{printed}}}")
    LaTeXTranslator.visit_math_block(translator, node)


def setup(app):
    # The built-in toctree collector assigns figure numbers at priority 500.
    app.connect("env-get-updated", number_chapter_equations, priority=600)
    app.add_node(nodes.math_block, latex=(visit_latex_equation, None), override=True)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}
