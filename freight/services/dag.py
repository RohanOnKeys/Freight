from __future__ import annotations

import networkx as nx


def build_dag(pipeline: dict) -> nx.DiGraph:
    graph = nx.DiGraph()

    jobs = pipeline.get("jobs", {})

    for job_name in jobs:
        graph.add_node(job_name)

    for job_name, config in jobs.items():

        needs = config.get("needs", [])

        if isinstance(needs, str):
            needs = [needs]

        for dependency in needs:

            if dependency not in jobs:
                raise ValueError(
                    f"Job '{job_name}' depends on unknown job '{dependency}'"
                )

            graph.add_edge(dependency, job_name)

    return graph


def validate_dag(graph: nx.DiGraph) -> None:

    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Pipeline contains cyclic dependencies.")


def execution_order(graph: nx.DiGraph):

    return list(nx.topological_sort(graph))