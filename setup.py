from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="noirlab-query-tool",
    version="0.1.0",
    author="Erik Solhaug",
    author_email="",
    description="Automated ADQL query submission tool for NOIRLab's Data Lab portal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/noirlab-query-tool",
    py_modules=["submit_noirlab_adql", "make_noirlab_adql", "download_noirlab_results"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    keywords="astronomy noirlab datalab adql queries",
)
