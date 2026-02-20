"""Alternative import paths for the wizlight library.

The library provides several convenience modules (bulblibrary, scenes, rgbcw)
that re-export symbols from their canonical locations. This allows importing
from multiple module paths:

    from wizlight import wizlight, PilotBuilder, PilotParser
    from wizlight.bulb import PIR_SOURCE
    from wizlight.bulblibrary import BulbType, BulbClass, Features
    from wizlight.discovery import find_wizlights, DiscoveredBulb
    from wizlight.exceptions import WizLightConnectionError, WizLightTimeOutError
    from wizlight.scenes import get_id_from_scene_name
    from wizlight.rgbcw import hs2rgbcw, rgb2rgbcw

These all work because:
- __init__.py re-exports the main classes
- bulb.py defines PIR_SOURCE
- bulblibrary.py, scenes.py, rgbcw.py re-export from models, effects, color
- exceptions.py and discovery.py provide their symbols directly
"""

# This module exists as documentation. The actual re-exports are handled
# by bulblibrary.py, scenes.py, rgbcw.py, and the main __init__.py.
