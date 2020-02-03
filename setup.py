import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='littledarwin',
    version='0.5',
    url='https://littledarwin.parsai.net',
    author="Ali Parsai",
    author_email="ali.parsai@live.com",
    description="LittleDarwin Mutation Analysis Framework",
    long_description=long_description,
    long_description_content_type="text/plain",
    license='GNU GPLv3',
    packages=setuptools.find_packages(),
#   packages=['littledarwin', 'custom_antlr4', 'custom_antlr4.atn', 'custom_antlr4.dfa', 'custom_antlr4.tree', 'custom_antlr4.error', 'custom_antlr4.xpath'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.3',
)

