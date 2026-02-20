"""Exception hierarchy for wizlight."""


class WizLightError(Exception):
    """Base exception for all wizlight errors."""


class WizLightConnectionError(WizLightError):
    """Raised when a connection to a WiZ device fails."""


class WizLightTimeOutError(WizLightError):
    """Raised when a WiZ device does not respond within the timeout period."""


class WizLightNotKnownBulb(WizLightError):
    """Raised when a WiZ device's module type is not recognized."""


class WizLightInvalidParameter(WizLightError):
    """Raised when an invalid parameter is provided to PilotBuilder."""


class WizLightCommandError(WizLightError):
    """Raised when a WiZ device returns an error response."""
