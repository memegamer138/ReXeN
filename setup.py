"""
Setup script for ReXeN.
Installs the package and creates console script 'rexen'.
To install, run: pip install -e .
"""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="rexen",
    version="0.1.0",
    description="AI-Powered Bug Bounty Recon Assistant",
    author="memegamer138",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "rexen=rexen.cli:cli",
        ],
    },
    python_requires=">=3.11",
)