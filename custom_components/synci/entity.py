from __future__ import annotations

from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import SynciIntegrationDataUpdateCoordinator


class SynciEntity(CoordinatorEntity[SynciIntegrationDataUpdateCoordinator]):

  _attr_attribution = ATTRIBUTION

  def __init__(self, coordinator: SynciIntegrationDataUpdateCoordinator, account_id: str) -> None:
    super().__init__(coordinator)
    self._account_id = account_id

  @property
  def data(self) -> dict[str, Any]:
    """Shortcut to access coordinator data for the entity."""
    return self.coordinator.data[self._account_id]
