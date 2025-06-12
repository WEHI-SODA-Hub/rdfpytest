# rdfpytest

Framework for running tests over RDF data in Python

## Background

There are some testing vocabularies defined by W3C working groups.
In particular, the DAWG working ground developed a [testing system](https://www.w3.org/2001/sw/DataAccess/tests/README.html) originally designed for testing standards compliance for implementers of the SPARQL query language.
[This was adapted](https://w3c.github.io/data-shapes/data-shapes-test-suite/) to use for testing conformance with the SHACL validation language standard.
Although both of these scenarios were testing standards conformance, they are useful for writing tests that validate that your SHACL shapes work as expected.


## Installation

Install pytest and rdfpytest, e.g.

```bash
uv add pytest git+https://github.com/WEHI-SODA-Hub/rdfpytest
```

## Usage

rdfpytest will discover each file with the pattern `test_*_{ttl,jsonld,json-ld,json}`, such as `test_manifest.ttl`, `test_manifest.jsonld` etc.
These must be test manifests that follow [this specification](https://w3c.github.io/data-shapes/data-shapes-test-suite/).
For example, a JSON-LD test manifest might look like this:

```json
{
    "@context": {
        "mf": "http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#",
        "sh": "http://www.w3.org/ns/shacl#",
        "sht": "http://www.w3.org/ns/shacl-test#"
    },
    "@type": "mf:Manifest",
    "mf:entries": [
        {
            "@type": "sht:Validate",
            "mf:name": "Add your test name here",
            "mf:action": {
                "sht:shapesGraph": {"@id": "/path/to/shapes.ttl"},
                "sht:dataGraph": {"@id": "/path/to/data.ttl"}
            },
            "mf:result": {
                "@type": "sh:ValidationReport",
                "sh:conforms": true
            }
        }
    ]
}
```

* `sht:shapesGraph` and `sht:dataGraph` are URLs that point to the shapes and data graphs. Typically these will be files in your repository.
* `sh:conforms` describes whether you expect the data to validate successfully (`true`) or unsuccessfully (`false`)
* `mf:name` is used to name the pytest cases that get generated

## Customization

`rdfpytest` supports the use of non-standard IRIs that can be used to configure the testing, based on extra parameters that `pySHACL` accepts. These IRIs should be attached to the `sht:Validate` entity. These all have the prefix `https://w3id.org/WEHI-SODA-Hub/rdfpytest` combined with the [Python parameter name](https://github.com/RDFLib/pySHACL?tab=readme-ov-file#python-module-use). 

For example if you wanted `INFO` severity validations to not cause the test failures:
```json
{
    "@context": {
        ...,
        "rpt:" "https://w3id.org/WEHI-SODA-Hub/rdfpytest"
    },
    "@type": "sht:Validate",
    "rpt:allow_infos": true
    ...
}
```

Or, if you wanted to only validate a subset of all the validation shapes, you could use
```json
{
    "@context": {
        ...,
        "rpt:" "https://w3id.org/WEHI-SODA-Hub/rdfpytest"
    },
    "@type": "sht:Validate",
    "rpt:use_shapes": [
        "some_iri",
        "other_iri
    ]
    ...
}
```
