import json
import time
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry
from urban_arrow_api import Bike, BikeSummary, Telemetry, Token

from custom_components.urban_arrow.const import CONF_TOKEN, DOMAIN

FIXTURES = Path(__file__).parent / "fixtures"
USERNAME = "rider@example.com"
PASSWORD = "secret"
BIKE_ID = "00000000-0000-0000-0000-000000000001"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def make_token(access: str = "access") -> Token:
    return Token(access, "refresh", time.time() + 3600)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    return


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title=USERNAME,
        unique_id=USERNAME,
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            CONF_TOKEN: make_token().as_dict(),
        },
    )


@pytest.fixture
def mock_client() -> Generator[AsyncMock]:
    bike = load_fixture("bike.json")
    with patch("custom_components.urban_arrow.UrbanArrowClient", autospec=True) as cls:
        client = cls.return_value
        client.get_bikes.return_value = [
            BikeSummary.parse({"id": BIKE_ID, "isStolen": False, **bike["details"]})
        ]
        client.get_bike.return_value = Bike.parse(bike)
        client.get_telemetry.return_value = Telemetry.parse(load_fixture("telemetry.json"))
        yield client


@pytest.fixture
def mock_login() -> Generator[AsyncMock]:
    with patch(
        "custom_components.urban_arrow.config_flow.login_with_credentials",
        return_value=make_token(),
    ) as login:
        yield login
