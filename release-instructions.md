## Release instructions

This section is only relevant for core developers.


## Setting version of a new release

To create a new release, first check whether the `VERSION` in [setup.py](setup.py) matches with the latest tag or PyPI release. 

If the version is the same then you need to bump the version to make a new release. 
Follow Semantic Versioning guidelines to decide whether the bump in version is major or minor.

If you did bump the version then run the following commands:


```sh
TAG=`python setup.py --version`
git add setup.py
git commit --message="Bump version to $TAG in preparation of a release"
git push
git tag --annotate $TAG --message="Release $TAG"
git push --tags
  ```


### Releasing on PyPI

To ensure this is successful, make sure you have relevant permissions to BMT package on [PyPI](https://pypi.org/project/bmt/).

Also, be sure to install [twine](https://pypi.org/project/twine/) and [wheel](https://pypi.org/project/wheel/)

Now, run the following commands:

```sh
rm -rf dist/
python setup.py sdist bdist_wheel
twine upload --repository-url https://upload.pypi.org/legacy/ --username PYPI_USERNAME dist/*
```
