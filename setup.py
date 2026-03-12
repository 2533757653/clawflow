from setuptools import setup, find_packages

setup(
    name="clawflow",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyyaml>=6.0",
        "click>=8.0",
        "rich>=13.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "clawflow=clawflow.cli:main",
        ],
    },
)
