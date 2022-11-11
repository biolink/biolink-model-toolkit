[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)]()
[![PyPI](https://img.shields.io/pypi/v/bmt)](https://img.shields.io/pypi/v/bmt)

# Biolink Model Toolkit

Biolink Model Toolkit (BMT): A Python API for working with the [Biolink Model](https://github.com/biolink/biolink-model).

BMT provides utility functions to look up Biolink Model for classes, relations, and properties based on Biolink CURIEs
or external CURIEs that have been mapped to Biolink Model.

> Note: Each release of BMT is pinned to a specific version of the Biolink Model to ensure consistency.

## Usage

BMT provides convenience methods to operate on the Biolink Model.

Using this toolkit you can,
- Get Biolink Model elements corresponding to a given Biolink class or slot name
- Get Biolink Model elements corresponding to a given external CURIE/IRI
- Get ancestors for a given Biolink Model element
- Get descendants for a given Biolink Model element
- Get parent for a given Biolink Model element
- Get children for a given Biolink Model element
- Check whether a given Biolink Model element is part of a specified subset