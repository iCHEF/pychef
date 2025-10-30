"""
Python utilities for iCHEF.

Released under the MIT license.
"""

__version__ = "0.0.0"

try:
    # pychef[aws] extra check
    from boto3 import __version__ as BOTO3_VERSION  # noqa: F401

    from .aws import *  # noqa: F401, F403
except ImportError:
    pass
