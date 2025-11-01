# setup.py
from setuptools import setup, find_packages

setup(
    name="reflection",
    version="0.0.0",
    packages=find_packages(where="."),      # find modules, modules.models, modules.agent, etc.
    package_dir={"": "."},                   # root of packages is the project root
    install_requires=[],                     # you can list core dependencies here
)
