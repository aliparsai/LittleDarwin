"""
Package metadata for MediumDarwin.

Important: keep this module lightweight to avoid circular imports (the core modules
import shared utilities that also live under this package).
"""

__author__ = "Ali Parsai"
__package__ = "littledarwin"
__license__ = "GNU GPLv3"
__url__ = "https://littledarwin.parsai.net/"


def __getattr__(name):
    # Lazy exports to avoid import-time cycles.
    if name == "MediumDarwin":
        from .MediumDarwin import MediumDarwin as _MD

        return _MD
    if name == "__version__":
        from .MediumDarwin import MediumDarwin as _MD

        return _MD.littleDarwinVersion
    raise AttributeError(name)


__all__ = ["MediumDarwin", "__version__"]
