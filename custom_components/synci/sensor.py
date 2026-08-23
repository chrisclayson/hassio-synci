from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override, Callable, Any

from dateutil.parser import isoparse
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .entity import SynciEntity

if TYPE_CHECKING:
  from homeassistant.core import HomeAssistant
  from homeassistant.helpers.entity_platform import AddEntitiesCallback

  from .coordinator import SynciIntegrationDataUpdateCoordinator
  from .data import SynciIntegrationConfigEntry

@dataclass(frozen=True, kw_only=True)
class SynciSensorEntityDescription(SensorEntityDescription):
  """Describes Monzo sensor entity."""

  value_fn: Callable[[dict[str, Any]], StateType]
  icon_fn: Callable[[dict[str, Any]], str] | None = None
  uom_fn: Callable[[dict[str, Any]], str] | None = None

ACCOUNT_SENSORS = [
  SynciSensorEntityDescription(
    key="balance",
    name="Balance",
    icon_fn=lambda data: "mdi:cash" if data["currency"] is None else "mdi:currency-" + data["currency"].lower(),
    value_fn=lambda data: data["balance"],
    uom_fn=lambda data: data["currency"].lower(),
    device_class=SensorDeviceClass.MONETARY,
    suggested_display_precision=2,
  ),
  SynciSensorEntityDescription(
    key="type",
    name="Account Type",
    icon="mdi:bank",
    value_fn=lambda data: data["cash_account_type"],
  ),
  SynciSensorEntityDescription(
    key="health",
    name="Connection Health",
    icon="mdi:account-heart",
    value_fn=lambda data: data["status"],
  ),
  SynciSensorEntityDescription(
    key="last_sync",
    name="Last Sync",
    icon="mdi:account-clock",
    value_fn=lambda data: isoparse(data["balances_last_synced_at"]),
    device_class=SensorDeviceClass.TIMESTAMP,
  ),
]

async def async_setup_entry(
  hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
  entry: SynciIntegrationConfigEntry,
  async_add_entities: AddEntitiesCallback,
) -> None:
  for account_id, account in entry.runtime_data.coordinator.data.items():
    device_info = DeviceInfo(
      entry_type=DeviceEntryType.SERVICE,
      configuration_url=f"https://app.synci.io/banks/accounts/{account["id"]}",
      identifiers={(
        DOMAIN,
        str(account["id"]),
      )},
      name=account["custom_name"] or account["details"] or account["institution_name"],
      manufacturer=account["institution_name"],
      model=account["name"],
    )
    async_add_entities([
      SynciSensor(
        coordinator=entry.runtime_data.coordinator,
        entity_description=sensor,
        account_id=account_id,
        device_info=device_info,
      )
      for sensor in ACCOUNT_SENSORS]
    )

class SynciSensor(SynciEntity, SensorEntity):

  entity_description: SynciSensorEntityDescription

  def __init__(
    self,
    coordinator: SynciIntegrationDataUpdateCoordinator,
    entity_description: SynciSensorEntityDescription,
    account_id: str,
    device_info: DeviceInfo,
  ) -> None:
    super().__init__(coordinator, account_id)
    self._attr_device_info = device_info
    self._attr_unique_id = f"{account_id}_{entity_description.key}"
    self.entity_description = entity_description

  @property
  @override
  def native_value(self) -> StateType:
    try:
      state = self.entity_description.value_fn(self.data)
    except KeyError, ValueError:
      return None

    return state

  @property
  @override
  def icon(self) -> str | None:
    if self.entity_description.icon_fn:
      try:
        return self.entity_description.icon_fn(self.data)
      except KeyError, ValueError:
        return None

    return self.entity_description.icon

  @property
  @override
  def native_unit_of_measurement(self) -> str | None:
    if self.entity_description.icon_fn:
      try:
        return self.entity_description.uom_fn(self.data)
      except KeyError, ValueError:
        return None

    return self.entity_description.unit_of_measurement
