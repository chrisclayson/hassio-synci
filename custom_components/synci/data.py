"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from homeassistant.config_entries import ConfigEntry
  from homeassistant.loader import Integration

  from .api import SynciIntegrationApiClient
  from .coordinator import SynciIntegrationDataUpdateCoordinator


type SynciIntegrationConfigEntry = ConfigEntry[SynciIntegrationData]


@dataclass
class SynciIntegrationData:

  client: SynciIntegrationApiClient
  coordinator: SynciIntegrationDataUpdateCoordinator
  integration: Integration
