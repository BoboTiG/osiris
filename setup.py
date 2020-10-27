"""Osiris."""
from setuptools import setup

from osiris import __version__ as version

with open("README.md") as f:
    description = f.read()

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
]
config = {
    "name": "osiris",
    "version": version,
    "author": "Tiger-222",
    "author_email": "contact@tiger-222.fr",
    "maintainer": "Tiger-222",
    "maintainer_email": "contact@tiger-222.fr",
    "url": "https://github.com/BoboTiG/python-mss",
    "description": (
        "An ultra fast cross-platform multiple screenshots module "
        "in pure python using ctypes."
    ),
    "long_description": description,
    "classifiers": classifiers,
    "packages": ["osiris"],
    "entry_points": {"console_scripts": ["osiris=osiris.__main__:main"]},
    "license": "MIT",
}

setup(**config)
