# rdfpytest

Framework for running tests over RDF data in Python

## Background

There are some testing vocabularies defined by W3C working groups.
In particular, the DAWG working ground developed a [testing system](https://www.w3.org/2001/sw/DataAccess/tests/README.html) originally designed for testing standards compliance for implementers of the SPARQL query language.
[This was adapted](https://w3c.github.io/data-shapes/data-shapes-test-suite/) to use for testing conformance with the SHACL validation language standard.
Although both of these scenarios were testing standards conformance, they are useful for writing tests that validate that your SHACL shapes work as expected.
