"""
Refer to https://github.com/w3c/data-shapes/tree/gh-pages/data-shapes-test-suite/tests
for example test structures
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterator
import pytest
from pathlib import Path
from _pytest.nodes import Node, Item, Collector
from rdflib import Graph, Namespace, RDF, SH
from rdfnav import GraphNavigator, UriNode
from urllib.parse import urlparse
from pyshacl import validate

MF = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#")
DAWGT = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-dawg#")
QT = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-query#")
SHT = Namespace("http://www.w3.org/ns/shacl-test#")

def uri_to_path(uri: str) -> Path:
    """Convert a URI to a local file path."""
    parse_result = urlparse(uri)
    return Path(parse_result.path)

def pytest_collect_file(parent: Node, file_path: Path):
    if file_path.suffix in {".ttl", ".json", ".json-ld"} and file_path.name.startswith("test"):
        return RdfTestManifest.from_parent(parent, path=file_path)

class RdfTestManifest(pytest.File):
    """A pytest File that represents a test manifest file."""

    def collect(self) -> Iterator[Item | Collector]:
        graph = Graph().parse(str(self.fspath))
        nav = GraphNavigator(graph)
        for manifest in nav.subjects(RDF.type, MF.Manifest):
            yield from self.yield_tests(manifest)

    def yield_tests(self, manifest: UriNode) -> Iterator[Item | Collector]:
        for sub_manifest in manifest.ref_objs(MF.include):
            yield RdfTestManifest.from_parent(self, path=uri_to_path(str(sub_manifest.iri)))
        for test_case in manifest.ref_objs(MF.entries):
            yield RdfTestCase.from_parent(
                self,
                node=test_case
            )

class RdfTestCase(pytest.Item):
    node: UriNode

    def __init__(self, *, node: UriNode, **kwargs: Any):
        super().__init__(**kwargs)
        self.node = node

    def runtest(self):
        action = self.node.ref_obj(MF.action)
        shapes_graph = action.ref_obj(SHT.shapesGraph)
        data_graph = action.ref_obj(SHT.dataGraph)
        expected_result = self.node.ref_obj(MF.result)
        conforms, results_graph, _ = validate(
            data_graph=Graph().parse(uri_to_path(str(data_graph.iri))),
            shacl_graph=Graph().parse(uri_to_path(str(shapes_graph.iri))),
            inference='rdfs',
            debug=True,
            allow_warnings=True,
            abort_on_error=False,
        )
        if not isinstance(results_graph, Graph):
            raise Exception(
                "SHACL validation did not return a valid results graph."
            )
        if conforms != expected_result.lit_obj(SHT.conforms):
            raise ShaclException(
                actual=GraphNavigator(results_graph).subject(RDF.type, SHT.ValidationReport),
                expected=expected_result
            )

    # def repr_failure(
    #     self,
    #     excinfo: pytest.ExceptionInfo[BaseException],
    #     # style: TracebackStyle | None = None,
    # ) -> str:
    #     """Called when self.runtest() raises an exception."""
    #     if isinstance(excinfo.value, ShaclException):
    #         return "\n".join(
    #             [
    #                 "usecase execution failed",
    #                 "   spec failed: {1!r}: {2!r}".format(*excinfo.value.args),
    #                 "   no further details known at this point.",
    #             ]
    #         )
    #     return super().repr_failure(excinfo)

@dataclass
class ShaclException(Exception):
    #: The result of the SHACL validation
    actual: UriNode
    #: The expected validation report
    expected: UriNode

    def __str__(self):
        return "".join([
            "SHACL validation failed.",
            "Actual validation results:",
            *[result.lit_obj(SH.value) for result in self.actual.ref_objs(SH.result)],
            "Expected validation results:",
            *[result.lit_obj(SH.value) for result in self.expected.ref_objs(SH.result)]
        ])
