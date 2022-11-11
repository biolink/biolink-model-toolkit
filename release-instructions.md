## Release instructions

- update the "REMOTE_PATH" variable in toolkit.py to reflect any updates in Biolink Model that 
should be reflected in the bmt release.
- Generate a release via the GitHub UI
- Use semantic versioning, prefixing with a 'v' (e.g. v0.8.12) in the GitHub release 
name and tag name

### Releasing on PyPI

The release-pypi.yml workflow will automatically release to PyPI when a new release is created on
GitHub. 


