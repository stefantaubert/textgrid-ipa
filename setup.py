"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
Modified by Madoshakalaka@Github (dependency links added)
"""

# io.open is needed for projects that support Python 2.7
# It ensures open() defaults to text mode with universal newlines,
# and accepts an argument to specify the text encoding
# Python 3 only projects can skip this import
from io import open
from os import path

# Always prefer setuptools over distutils
from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
  long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name="textgrid_tools",
    version="1.0.0",
    url="https://github.com/stefantaubert/textgrid_ipa.git",
    author="Stefan Taubert",
    author_email="stefan.taubert@posteo.de",
    description="Utils for TextGrid processing",
    packages=["textgrid_tools"],
    install_requires=[
        "click==7.1.2; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
        "dragonmapper==0.2.6",
        "editdistance==0.5.3",
        "epitran==1.8",
        "hanzidentifier==1.0.2",
        "inflect==5.0.2; python_version >= '3.6'",
        "ipapy==0.0.9.0",
        "joblib==1.0.0; python_version >= '3.6'",
        "llvmlite==0.35.0; python_version >= '3.6'",
        "marisa-trie==0.7.5",
        "munkres==1.1.4",
        "nltk==3.5",
        "numba==0.52.0; python_version >= '3.6' and python_version < '3.9'",
        "numpy==1.19.5",
        "pandas==1.2.0",
        "panphon==0.17",
        "python-dateutil==2.8.1; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "pytz==2020.5",
        "pyyaml==5.3.1",
        "regex==2020.11.13",
        "resampy==0.2.2",
        "scipy==1.6.0",
        "six==1.15.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "textgrid==1.5",
        "tqdm==4.54.0",
        "unicodecsv==0.14.1",
        "unidecode==1.1.2",
        "wget==3.2",
        "zhon==1.1.5",
    ],
    dependency_links=[
        "git+https://github.com/stefantaubert/audio-utils.git@2bc4735ce7e0f73928d026bf2d1504b03b1aa67b#egg=audio-utils",
        "git+https://github.com/stefantaubert/cmudict-parser.git@1c4cce798af0f76e882f3083ce382ff1317ecc96#egg=cmudict-parser",
        "git+https://github.com/stefantaubert/text-utils.git@a93a8a3c27e693b01fa734de3c9f5be53154c04e#egg=text-utils",
    ],
)
