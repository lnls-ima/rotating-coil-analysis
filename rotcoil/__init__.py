"""Rotating coil analysis package."""

from . import data_file
from . import multipole_errors_spec
from . import pdf_report
from . import utils

import os

with open(os.path.join(__path__[0], 'VERSION'), 'r') as _f:
    __version__ = _f.read().strip()

del os
