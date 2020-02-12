from setuptools import setup, find_packages

version = '0.1.1'

requires = [
    "biolinkml>=1.3.6"
]

setup(
    name='bmt',
    version=version,
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/lhannest/biolink-model-toolkit',
    install_requires=requires,
    python_requires='>=3.7',
    description='Biolink Model Toolkit - a collection of python functions for using the biolink model '
                '(https://github.com/biolink/biolink-model)'
)
