"""Fold source code in HTML while keeping outputs and the PDF unchanged."""
from docutils import nodes
from sphinx.transforms.post_transforms import SphinxPostTransform


class FoldCode(SphinxPostTransform):
    default_priority = 700
    formats = ("html",)

    def run(self, **kwargs):
        for block in list(self.document.findall(nodes.literal_block)):
            ancestor = block.parent
            while ancestor is not None:
                # MyST-NB text outputs are also literal blocks, but should stay visible.
                if "cell_output" in ancestor.get("classes", []):
                    break
                ancestor = ancestor.parent
            else:
                wrapper = nodes.container(classes=["course-code-fold-wrapper"])
                block.replace_self(wrapper)
                wrapper += nodes.raw(
                    "", '<details class="course-code-fold"><summary>Code</summary>',
                    format="html",
                )
                wrapper += block
                wrapper += nodes.raw("", "</details>", format="html")


def setup(app):
    app.add_post_transform(FoldCode)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}
