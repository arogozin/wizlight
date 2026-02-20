"""Tests for the wizlight bulb class."""

import pytest

from wizlight.bulb import PIR_SOURCE, wizlight
from wizlight.models import BulbClass
from wizlight.pilot import PilotBuilder

from .conftest import MockUDPClient


@pytest.fixture
def bulb(mock_client: MockUDPClient) -> wizlight:
    """Create a wizlight instance with a mock client."""
    b = wizlight("192.168.1.100", client=mock_client)
    return b


class TestWizlight:
    @pytest.mark.asyncio
    async def test_update_state(self, bulb: wizlight):
        state = await bulb.updateState()
        assert state.get_state() is True
        assert state.get_brightness() == 128
        assert bulb.mac == "a8bb50aabbcc"

    @pytest.mark.asyncio
    async def test_status_property(self, bulb: wizlight):
        assert bulb.status is False  # No state fetched yet
        await bulb.updateState()
        assert bulb.status is True

    @pytest.mark.asyncio
    async def test_get_bulbtype(self, bulb: wizlight):
        bt = await bulb.get_bulbtype()
        assert bt.bulb_type == BulbClass.RGB
        assert bt.fw_version == "1.30.0"
        assert "SHRGB" in bt.name

    @pytest.mark.asyncio
    async def test_get_mac(self, bulb: wizlight):
        mac = await bulb.getMac()
        assert mac == "a8bb50aabbcc"

    @pytest.mark.asyncio
    async def test_turn_on(self, bulb: wizlight, mock_client: MockUDPClient):
        pilot = PilotBuilder(scene="Club", brightness=200)
        await bulb.turn_on(pilot)
        sent = mock_client.sent_messages[-1]
        assert sent["method"] == "setPilot"
        assert sent["params"]["sceneId"] == 26
        assert sent["params"]["dimming"] == 200

    @pytest.mark.asyncio
    async def test_turn_off(self, bulb: wizlight, mock_client: MockUDPClient):
        await bulb.turn_off()
        sent = mock_client.sent_messages[-1]
        assert sent["method"] == "setPilot"
        assert sent["params"]["state"] is False

    @pytest.mark.asyncio
    async def test_get_supported_scenes(self, bulb: wizlight):
        scenes = await bulb.getSupportedScenes()
        assert "Club" in scenes
        assert "Fireplace" in scenes
        assert "Spring" in scenes
        assert len(scenes) == 37

    @pytest.mark.asyncio
    async def test_get_system_config(self, bulb: wizlight):
        config = await bulb.get_system_config()
        assert config["moduleName"] == "ESP01_SHRGB3_01ABI"
        assert config["fwVersion"] == "1.30.0"

    @pytest.mark.asyncio
    async def test_set_speed(self, bulb: wizlight, mock_client: MockUDPClient):
        await bulb.set_speed(150)
        sent = mock_client.sent_messages[-1]
        assert sent["params"]["speed"] == 150

    @pytest.mark.asyncio
    async def test_set_ratio(self, bulb: wizlight, mock_client: MockUDPClient):
        await bulb.set_ratio(50)
        sent = mock_client.sent_messages[-1]
        assert sent["params"]["ratio"] == 50

    @pytest.mark.asyncio
    async def test_get_power(self, bulb: wizlight):
        power = await bulb.get_power()
        assert power == 8.5

    @pytest.mark.asyncio
    async def test_diagnostics(self, bulb: wizlight):
        await bulb.updateState()
        await bulb.get_bulbtype()
        diag = bulb.diagnostics
        assert diag["ip"] == "192.168.1.100"
        assert diag["mac"] == "a8bb50aabbcc"
        assert "bulb_type" in diag

    @pytest.mark.asyncio
    async def test_async_close_alias(self, bulb: wizlight):
        await bulb.async_close()  # Should not raise

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_client: MockUDPClient):
        async with wizlight("192.168.1.100", client=mock_client) as bulb:
            await bulb.updateState()
            assert bulb.status is True


def test_pir_source_constant():
    assert PIR_SOURCE == "pir"
