from setuptools import setup, find_packages

setup(
    name='latin_macronizer',
    version='1.0',
    packages=find_packages(),
    scripts=['scripts/macronize.py'],
)
