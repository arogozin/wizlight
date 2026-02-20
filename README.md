# wizlight

Full-featured async Python library for WiZ smart lights.

Complete WiZ protocol support with all 36+ built-in effects, device discovery, push state updates, and a Home Assistant integration.

## Install

```bash
pip install wizlight
```

## Quick Start

```python
from wizlight import wizlight, PilotBuilder

async with wizlight("192.168.1.100") as bulb:
    # Turn on with Fireplace effect at 80% brightness
    await bulb.turn_on(PilotBuilder(scene="Fireplace", brightness=200))

    # Check state
    state = await bulb.updateState()
    print(state.get_scene_name())  # "Fireplace"

    # Turn off
    await bulb.turn_off()
```

## CLI

```bash
wizlight discover
wizlight state 192.168.1.100
wizlight on 192.168.1.100 --scene Fireplace --brightness 200
wizlight off 192.168.1.100
wizlight effects
```

## Home Assistant

Install via HACS as a custom WiZ integration.

## License

MIT
