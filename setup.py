from setuptools import setup, find_packages

with open("requirements.txt", "r") as FH:
    REQUIREMENTS = FH.readlines()

NAME = 'bmt'
VERSION = '0.8.2'
DESCRIPTION = 'Biolink Model Toolkit: A Python API for working with the Biolink Model'
URL = 'https://github.com/biolink/biolink-model-toolkit'
AUTHOR = 'Deepak Unni', 'Sierra Moxon'
EMAIL = 'smoxon@lbl.gov'
REQUIRES_PYTHON = '>=3.7'
LICENSE = 'BSD'

setup(
    name=NAME,
    author=AUTHOR,
    version=VERSION,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license=LICENSE,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    install_requires=[r for r in REQUIREMENTS if not r.startswith("#")],
    keywords='NCATS NCATS-Translator Biolink-Model',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3'
    ],
)
