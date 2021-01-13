# <pep8 compliant>

from .xmodel import Model
from .xanim import Anim
from .sanim import SiegeAnim

__version__ = (0, 3, 0)  # Version specifier for PyCoD

# Included for support with legacy versions
version = __version__

assert Model
assert Anim
assert SiegeAnim
