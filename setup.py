from setuptools import setup

setup(
    name='littledarwin',
    version='0.5',
    packages=['littledarwin', 'custom_antlr4', 'custom_antlr4.atn', 'custom_antlr4.dfa', 'custom_antlr4.tree',
              'custom_antlr4.error', 'custom_antlr4.xpath'],
    url='https://littledarwin.parsai.net',
    license='GNU GPLv3',
    author='Ali Parsai',
    author_email='ali@parsai.net',
    description='LittleDarwin Mutation Testing Tool'
)
