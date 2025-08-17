#!/usr/bin/env python3

"""
__main__ script for littledarwin package
"""

from littledarwin import LittleDarwin
import sys


def entryPoint():
    """
    This function is the entry point for the ``littledarwin`` package when it
    is run as a module.
    """
    LittleDarwin.main()


if __name__ == "__main__":
    sys.exit(entryPoint())
