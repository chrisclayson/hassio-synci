from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import LOGGER
from .api import (
  SynciIntegrationApiClientAuthenticationError,
  SynciIntegrationApiClientError,
  SynciIntegrationApiClientRateLimitError,
)
import json

if TYPE_CHECKING:
  from .data import SynciIntegrationConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class SynciIntegrationDataUpdateCoordinator(DataUpdateCoordinator):

  config_entry: SynciIntegrationConfigEntry

  async def _async_update_data(self) -> Any:
    """Update data via library."""
    try:
      data = {}
      connections = await self.config_entry.runtime_data.client.async_get_data()
      for c in connections:
        connection = await self.config_entry.runtime_data.client.async_get_connection_data(c["id"])

        for account in connection["financial_accounts"]:
          LOGGER.debug(f"Parsing account details {json.dumps(account)}")

          if "balance" in account and "available" in account["balance"]:
            data.update({
              str(account["id"]): {
                "id": account["id"],
                "institution_id": c["id"],
                "institution_name": connection["institution"]["name"],
                "external_id": connection["institution"]["external_id"],
                "logo": connection["institution"]["logo"],
                "updated_at": connection["institution"]["updated_at"],
                "enabled": account["enabled"],
                "account_category": account["account_category"],
                "name": account["name"],
                "custom_name": account["custom_name"],
                "display_name": account["display_name"],
                "iban": account["iban"],
                "bic": account["bic"],
                "owner_name": account["owner_name"],
                "currency": account["currency"],
                "details": account["details"],
                "balances_last_synced_at": account["balances_last_synced_at"],
                "balance": account["balance"]["available"],
                "status": account["health"]["status"],
                "cash_account_type": account["cash_account_type"],
              }
            })

      return data
    except SynciIntegrationApiClientAuthenticationError as exception:
      raise ConfigEntryAuthFailed(exception) from exception
    except SynciIntegrationApiClientRateLimitError as exception:
      raise UpdateFailed(
        exception,
        retry_after=exception.retry_after,
      ) from exception
    except SynciIntegrationApiClientError as exception:
      raise UpdateFailed(exception) from exception
