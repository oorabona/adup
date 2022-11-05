from setuptools import setup
from versioningit import get_cmdclasses

setup(
    cmdclass=get_cmdclasses(),
    name="adup",
    package_dir={"": "src"},
)
