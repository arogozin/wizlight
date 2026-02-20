"""wizlight — Full-featured async Python library for WiZ smart lights.

Usage:
    from wizlight import wizlight, PilotBuilder, PilotParser

    async with wizlight("192.168.1.100") as bulb:
        await bulb.turn_on(PilotBuilder(scene="Fireplace", brightness=200))
        state = await bulb.updateState()
        print(state.get_brightness())
"""

from wizlight.bulb import PIR_SOURCE, wizlight
from wizlight.discovery import discover, discover_mdns, find_wizlights
from wizlight.effects import SCENES, get_id_from_scene_name, get_scene_name
from wizlight.exceptions import (
    WizLightCommandError,
    WizLightConnectionError,
    WizLightError,
    WizLightInvalidParameter,
    WizLightNotKnownBulb,
    WizLightTimeOutError,
)
from wizlight.models import (
    BulbClass,
    BulbType,
    DiscoveredBulb,
    Features,
    FirmwareInfo,
    KelvinRange,
)
from wizlight.pilot import PilotBuilder, PilotParser
from wizlight.push import PushManager

__version__ = "0.1.0"

__all__ = [
    # Main class
    "wizlight",
    # Command/state
    "PilotBuilder",
    "PilotParser",
    # Models
    "BulbClass",
    "BulbType",
    "DiscoveredBulb",
    "Features",
    "FirmwareInfo",
    "KelvinRange",
    # Discovery
    "discover",
    "discover_mdns",
    "find_wizlights",
    # Effects
    "SCENES",
    "get_id_from_scene_name",
    "get_scene_name",
    # Push
    "PushManager",
    # Exceptions
    "WizLightCommandError",
    "WizLightConnectionError",
    "WizLightError",
    "WizLightInvalidParameter",
    "WizLightNotKnownBulb",
    "WizLightTimeOutError",
    # Constants
    "PIR_SOURCE",
    # Version
    "__version__",
]
