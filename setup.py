# setup.py
from setuptools import setup, find_packages
setup(name="citi_bike_etl", version="0.1", packages=find_packages(where="src"), package_dir={"": "src"})