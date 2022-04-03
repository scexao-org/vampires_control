from setuptools import setup, find_packages
import os
import re

version = ""

with open(os.path.join("vampires_control", "__init__.py"), "r") as fh:
    for line in fh.readlines():
        m = re.search("__version__ = [\"'](.+)[\"']", line)
        if m:
            version = m.group(1)


with open("README.md", "r") as fh:
    readme = fh.read()

setup(
    long_description=readme,
    long_description_content_type="text/markdown",
    name="vampires-control",
    version=version,
    description="VAMPIRES control software",
    python_requires=">=3.7,<3.10",
    project_urls={
        "repository": "https://github.com/scexao-org/vampires-control",
    },
    author="Miles Lucas",
    author_email="mdlucas@hawaii.edu",
    maintainer="Miles Lucas <mdlucas@hawaii.edu",
    license="MIT",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    package_data={},
    scripts=[
        "scripts/vampires_beamsplitter",
        "scripts/vampires_diffwheel",
        "scripts/conex"
    ],
    install_requires=[
        "tqdm==4.*",
    ],
)
