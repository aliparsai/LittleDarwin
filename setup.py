import setuptools
import littledarwin

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='littledarwin',
    version=littledarwin.__version__,
    url=littledarwin.__url__,
    author=littledarwin.__author__,
    author_email="ali.parsai@live.com",
    description="LittleDarwin Mutation Analysis Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='GNU GPLv3',
    packages=setuptools.find_packages(),
    install_requires=['graphviz', 'pygments'],
    entry_points={'console_scripts': ['littledarwin=littledarwin.__main__:entryPoint', ], },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)

