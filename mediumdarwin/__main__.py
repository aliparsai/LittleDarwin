#!/usr/bin/env python3

"""
__main__ script for littledarwin package
"""

from mediumdarwin import MediumDarwin
import sys
import os


def entryPoint():
    ld = MediumDarwin()
    ld.main()


if __name__ == "__main__":
    sys.exit(entryPoint())
