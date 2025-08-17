Usage
=====

This guide explains how to install and use LittleDarwin.

Installation
------------

You can install LittleDarwin using ``pip``:

.. code-block:: bash

    pip install littledarwin

Running LittleDarwin
--------------------

You can run LittleDarwin as a Python module:

.. code-block:: bash

    python3 -m littledarwin [options]

LittleDarwin has two main phases:

*   **Mutation phase:** In this phase, LittleDarwin generates mutants of your
    Java source code. To activate this phase, use the ``-m`` or ``--mutate``
    option.
*   **Build phase:** In this phase, LittleDarwin runs a build command for each
    mutant and checks if the build passes or fails. To activate this phase,
    use the ``-b`` or ``--build`` option.

You can run both phases in a single command, but it is recommended to run
them separately.

Command-Line Options
--------------------

Here is a list of the available command-line options:

.. program:: littledarwin

.. option:: -m, --mutate

    Activate the mutation phase.

.. option:: -b, --build

    Activate the build phase.

.. option:: -v, --verbose

    Verbose output.

.. option:: -p, --path <path>

    Path to source files.

.. option:: -t, --build-path <path>

    Path to build system working directory.

.. option:: -c, --build-command <command>

    Command to run the build system. If it includes more than a single
    argument, they should be separated by a comma. For example:
    ``mvn,clean,test``.

.. option:: --test-path <path>

    Path to test project build system working directory.

.. option:: --test-command <command>

    Command to run the test-suite. If it includes more than a single
    argument, they should be separated by a comma. For example:
    ``mvn,test``.

.. option:: --initial-build-command <command>

    Command to run the initial build.

.. option:: --timeout <seconds>

    Timeout value for the build process.

.. option:: --cleanup <command>

    Commands to run after each build.

.. option:: --use-alternate-database <path>

    Path to alternative database.

.. option:: --license

    Output the license and exit.

.. option:: --higher-order <order>

    Define order of mutation. Use -1 to dynamically adjust per class.

.. option:: --null-check

    Use null check mutation operators.

.. option:: --method-level

    Use method level mutation operators.

.. option:: --all

    Use all mutation operators.

.. option:: --whitelist <file>

    Analyze only included packages or files defined in this file (one
    package name or path to file per line).

.. option:: --blacklist <file>

    Analyze everything except packages or files defined in this file (one
    package name or path to file per line).

Examples
--------

Here are some examples of how to use LittleDarwin.

Generating Traditional Mutants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To generate traditional mutants for a project, you can use the following
command:

.. code-block:: bash

    python3 -m littledarwin -m -p /path/to/your/project/src/main -t /path/to/your/project

This will create a directory called ``LittleDarwinResults`` in your project's
root directory, which will contain the generated mutants.

Generating Higher-Order Mutants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To generate second-order mutants, you can use the ``--higher-order`` option:

.. code-block:: bash

    python3 -m littledarwin -m -p /path/to/your/project/src/main -t /path/to/your/project --higher-order=2

Running a Full Mutation Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run a full mutation analysis, you need to activate both the mutation and
build phases, and you need to provide a build command. For example, if you
are using Maven, you can use the following command:

.. code-block:: bash

    python3 -m littledarwin -m -b -p /path/to/your/project/src/main -t /path/to/your/project -c "mvn,clean,test" --timeout=600

This will first generate the mutants, and then it will run ``mvn clean test``
for each mutant. It will then generate a report of the results in the
``LittleDarwinResults`` directory.
