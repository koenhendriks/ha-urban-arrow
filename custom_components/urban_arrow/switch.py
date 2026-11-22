from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from urban_arrow_api import BikeSetting, UrbanArrowClient, UrbanArrowError

from .const import DOMAIN
from .coordinator import UrbanArrowBikeData
from .entity import UrbanArrowEntity
from .types import UrbanArrowConfigEntry

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class UrbanArrowSwitchEntityDescription(SwitchEntityDescription):
    is_on_fn: Callable[[UrbanArrowBikeData], bool | None]
    set_fn: Callable[[UrbanArrowClient, str, bool], Awaitable[None]]


def _setting(setting: BikeSetting) -> Callable[[UrbanArrowClient, str, bool], Awaitable[None]]:
    return lambda client, bike_id, enabled: client.set_setting(bike_id, setting, enabled)


def _module(attr: str) -> Callable[[UrbanArrowBikeData], bool | None]:
    return lambda data: getattr(data.bike.module, attr) if data.bike.module else None


def _notification(attr: str) -> Callable[[UrbanArrowBikeData], bool | None]:
    return lambda data: getattr(data.bike.notifications, attr) if data.bike.notifications else None


SWITCHES: tuple[UrbanArrowSwitchEntityDescription, ...] = (
    UrbanArrowSwitchEntityDescription(
        key="theft_protection",
        translation_key="theft_protection",
        is_on_fn=_module("protection_enabled"),
        set_fn=lambda client, bike_id, enabled: client.set_theft_protection(bike_id, enabled),
    ),
    UrbanArrowSwitchEntityDescription(
        key="auto_protection",
        translation_key="auto_protection",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=_module("auto_protection_enabled"),
        set_fn=_setting(BikeSetting.AUTO_PROTECTION),
    ),
    UrbanArrowSwitchEntityDescription(
        key="module_battery_management",
        translation_key="module_battery_management",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=_module("auto_charge_enabled"),
        set_fn=_setting(BikeSetting.MODULE_BATTERY_MANAGEMENT),
    ),
    UrbanArrowSwitchEntityDescription(
        key="notify_battery_full",
        translation_key="notify_battery_full",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        is_on_fn=_notification("battery_full"),
        set_fn=_setting(BikeSetting.NOTIFICATION_BATTERY_FULL),
    ),
    UrbanArrowSwitchEntityDescription(
        key="notify_battery_low",
        translation_key="notify_battery_low",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        is_on_fn=_notification("battery_low"),
        set_fn=_setting(BikeSetting.NOTIFICATION_BATTERY_LOW),
    ),
    UrbanArrowSwitchEntityDescription(
        key="notify_module_battery_low",
        translation_key="notify_module_battery_low",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        is_on_fn=_notification("module_battery_low"),
        set_fn=_setting(BikeSetting.NOTIFICATION_MODULE_BATTERY_LOW),
    ),
    UrbanArrowSwitchEntityDescription(
        key="notify_protection_activated",
        translation_key="notify_protection_activated",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        is_on_fn=_notification("protection_activated"),
        set_fn=_setting(BikeSetting.NOTIFICATION_PROTECTION_ACTIVATED),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UrbanArrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        UrbanArrowSwitch(coordinator, bike_id, description)
        for bike_id in coordinator.data
        for description in SWITCHES
    )


class UrbanArrowSwitch(UrbanArrowEntity, SwitchEntity):
    entity_description: UrbanArrowSwitchEntityDescription

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.is_on_fn(self.bike_data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set(False)

    async def _async_set(self, enabled: bool) -> None:
        try:
            await self.entity_description.set_fn(self.coordinator.client, self.bike_id, enabled)
        except UrbanArrowError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="action_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        await self.coordinator.async_request_refresh()
