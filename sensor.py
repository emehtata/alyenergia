from __future__ import annotations

from datetime import date

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AlyenergiaCoordinator

SENSORS = (
    ("current_consumption", "Current month consumption", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    ("current_cost", "Current month cost", "EUR", SensorDeviceClass.MONETARY, None),
    ("current_mean_price", "Current month mean price", "EUR/kWh", None, SensorStateClass.MEASUREMENT),
    ("previous_consumption", "Previous month consumption", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL),
    ("previous_cost", "Previous month cost", "EUR", SensorDeviceClass.MONETARY, None),
    ("previous_mean_price", "Previous month mean price", "EUR/kWh", None, SensorStateClass.MEASUREMENT),
    ("latest_daily_consumption", "Latest reported day consumption", "kWh", SensorDeviceClass.ENERGY, None),
    ("latest_reported_date", "Latest reported day", None, SensorDeviceClass.DATE, None),
    ("latest_invoice_balance", "Latest invoice balance", "EUR", SensorDeviceClass.MONETARY, None),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: AlyenergiaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlyenergiaSensor(coordinator, key, name, unit, device_class, state_class) for key, name, unit, device_class, state_class in SENSORS])


class AlyenergiaSensor(CoordinatorEntity[AlyenergiaCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: AlyenergiaCoordinator, key: str, name: str, unit: str, device_class: SensorDeviceClass | None, state_class: SensorStateClass | None) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"alyenergia_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._key) if self.coordinator.data else None
        return date.fromisoformat(value) if self._key == "latest_reported_date" and value else value

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.coordinator.entry.entry_id)}, name="Vihrea Alyenergia", manufacturer="Vihrea Alyenergia")
