import setuptools
from mediumdarwin import __author__, __url__, __version__, __license__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='mediumdarwin',
    version=__version__,
    url=__url__,
    author=__author__,
    author_email="hesamips@tcd.ie",
    description="MediumDarwin Mutation Analysis Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=__license__,
    packages=setuptools.find_packages(),
    install_requires=['antlr4-python3-runtime', 'graphviz'],
    entry_points={'console_scripts': [
        'mediumdarwin=mediumdarwin.__main__:entryPoint', ], },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    include_package_data=True
)
