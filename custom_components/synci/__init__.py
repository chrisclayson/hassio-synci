from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_API_TOKEN, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import SynciIntegrationApiClient
from .const import DOMAIN, LOGGER
from .coordinator import SynciIntegrationDataUpdateCoordinator
from .data import SynciIntegrationData, SynciIntegrationConfigEntry

if TYPE_CHECKING:
  from homeassistant.core import HomeAssistant

  from .data import SynciIntegrationData

PLATFORMS: list[Platform] = [
  Platform.SENSOR,
]


async def async_setup_entry(
  hass: HomeAssistant,
  entry: SynciIntegrationConfigEntry,
) -> bool:
  coordinator = SynciIntegrationDataUpdateCoordinator(
    hass=hass,
    logger=LOGGER,
    name=DOMAIN,
    update_interval=timedelta(minutes=30),
    config_entry=entry,
  )
  entry.runtime_data = SynciIntegrationData(
    client=SynciIntegrationApiClient(
      api_token=entry.data[CONF_API_TOKEN],
      session=async_get_clientsession(hass),
    ),
    integration=async_get_loaded_integration(hass, entry.domain),
    coordinator=coordinator,
  )
  await coordinator.async_config_entry_first_refresh()

  await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

  return True


async def async_unload_entry(
  hass: HomeAssistant,
  entry: SynciIntegrationConfigEntry,
) -> bool:
  return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
