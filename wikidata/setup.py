from setuptools import setup, find_packages

setup(
    name="wikidata",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rocksdict>=0.1.0",
        "pydantic-settings>=2.0.0",
        "pytest>=7.0.0",
    ],
    python_requires=">=3.8",
)
