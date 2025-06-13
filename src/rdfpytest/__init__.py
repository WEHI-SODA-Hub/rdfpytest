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
from rdflib import Graph, Namespace, SH
from rdfnav import GraphNavigator, UriNode
from urllib.parse import urlparse
from pyshacl import validate
from itertools import chain, groupby

MF = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#")
DAWGT = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-dawg#")
QT = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-query#")
SHT = Namespace("http://www.w3.org/ns/shacl-test#")
RPT = Namespace("https://w3id.org/WEHI-SODA-Hub/rdfpytest/")

def uri_to_path(uri: str) -> Path:
    """Convert a URI to a local file path."""
    parse_result = urlparse(uri)
    return Path(parse_result.path)

def pytest_collect_file(parent: Node, file_path: Path):
    if file_path.suffix in {".ttl", ".json", ".json-ld", ".jsonld"} and file_path.name.startswith("test"):
        return RdfTestManifest.from_parent(parent, path=file_path)

class RdfTestManifest(pytest.File):
    """A pytest File that represents a test manifest file."""

    def collect(self) -> Iterator[Item | Collector]:
        graph = Graph().parse(str(self.fspath))
        nav = GraphNavigator(graph)
        for manifest in nav.instances(MF.Manifest):
            yield from self.yield_tests(manifest)

    def yield_tests(self, manifest: UriNode) -> Iterator[Item | Collector]:
        for sub_manifest in manifest.ref_objs_via(MF.include):
            yield RdfTestManifest.from_parent(self, path=uri_to_path(str(sub_manifest.iri)))
        for test_case in manifest.ref_objs_via(MF.entries):
            yield RdfTestCase.from_parent(
                self,
                name=test_case.lit_obj_via(MF.name),
                node=test_case
            )

class RdfTestCase(pytest.Item):
    node: UriNode

    def __init__(self, *, node: UriNode, **kwargs: Any):
        super().__init__(**kwargs)
        self.node = node

    def runtest(self):
        action = self.node.ref_obj_via(MF.action)
        shapes_graph = action.ref_obj_via(SHT.shapesGraph)
        data_graph = action.ref_obj_via(SHT.dataGraph)
        expected_result = self.node.ref_obj_via(MF.result)

        validator_kwargs: dict[str, Any] = {} 

        # Add literal parameters specified using the RPT prefix
        literal_params = {
            "advanced",
            "inference",
            "inplace",
            "abort_on_first",
            "allow_infos",
            "allow_warnings",
            "max_validation_depth",
            "sparql_mode",
            "debug",
            "js",
            "meta_shacl",
            "iterate_rules",
            "check_dash_result",
            "do_owl_imports"
        }
        for pred, obj in self.node.lit_objs_sans_prefix(RPT):
            if pred not in literal_params:
                raise ValueError(f"Unknown parameter {pred} in test case {self.node.iri}")
            if pred in validator_kwargs:
                raise ValueError(f"Duplicate parameter {pred}")
            validator_kwargs[pred] = obj

        # Add URI params specified using the RPT prefix
        uri_params = {
            "focus_nodes",
            "use_shapes"
        }
        for pred, objs in groupby(self.node.ref_objs_sans_prefix(RPT), key=lambda x: x[0]):
            if pred not in uri_params:
                raise ValueError(f"Unknown parameter {pred} in test case {self.node.iri}")
            validator_kwargs[pred] = [str(obj.iri) for _, obj in objs]
        
        conforms, results_graph, _ = validate(
            data_graph=Graph().parse(uri_to_path(str(data_graph.iri))),
            shacl_graph=Graph().parse(uri_to_path(str(shapes_graph.iri))),
            **validator_kwargs
        )
        if not isinstance(results_graph, Graph):
            raise Exception(
                "SHACL validation did not return a valid results graph."
            )
        if conforms != expected_result.lit_obj_via(SH.conforms):
            raise ShaclException(
                actual=GraphNavigator(results_graph).instance(SH.ValidationReport),
                expected=expected_result
            )

@dataclass
class ShaclException(Exception):
    #: The result of the SHACL validation
    actual: UriNode
    #: The expected validation report
    expected: UriNode

    def __str__(self) -> str:
        return "\n".join([
            "SHACL validation failed.",
            "Actual validation report:",
            self.actual.subgraph().serialize(format='json-ld'),
            "Expected validation report:",
            self.expected.subgraph().serialize(format='json-ld'),
        ])
