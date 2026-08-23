from __future__ import annotations

import voluptuous as vol
import json
from homeassistant import config_entries
from homeassistant.const import CONF_API_TOKEN
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration
from slugify import slugify

from .api import (
  SynciIntegrationApiClient,
  SynciIntegrationApiClientAuthenticationError,
  SynciIntegrationApiClientCommunicationError,
  SynciIntegrationApiClientError,
)
from .const import DOMAIN, LOGGER


class SynciIntegrationFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
  VERSION = 1

  async def async_step_user(
    self,
    user_input: dict | None = None,
  ) -> config_entries.ConfigFlowResult:
    """Handle a flow initialized by the user."""
    _errors = {}
    if user_input is not None:
      try:
        await self._test_credentials(
          api_token=user_input[CONF_API_TOKEN],
        )
      except SynciIntegrationApiClientAuthenticationError as exception:
        LOGGER.warning(exception)
        _errors["base"] = "auth"
      except SynciIntegrationApiClientCommunicationError as exception:
        LOGGER.error(exception)
        _errors["base"] = "connection"
      except SynciIntegrationApiClientError as exception:
        LOGGER.exception(exception)
        _errors["base"] = "unknown"
      else:
        client = SynciIntegrationApiClient(
          api_token=user_input[CONF_API_TOKEN],
          session=async_get_clientsession(self.hass),
        )
        result = await client.async_get_user_data()
        await self.async_set_unique_id(
          unique_id="synci_" + str(result["id"])
        )
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
          title=result["email"],
          data=user_input,
        )

    integration = async_get_loaded_integration(self.hass, DOMAIN)
    assert integration.documentation is not None, (  # noqa: S101
      "Integration documentation URL is not set in manifest.json"
    )

    return self.async_show_form(
      step_id="user",
      description_placeholders={
        "documentation_url": integration.documentation,
      },
      data_schema=vol.Schema(
        {
          vol.Required(
            CONF_API_TOKEN,
            default=(user_input or {}).get(CONF_API_TOKEN, vol.UNDEFINED),
          ): selector.TextSelector(
            selector.TextSelectorConfig(
              type=selector.TextSelectorType.TEXT,
            ),
          ),
        },
      ),
      errors=_errors,
    )

  async def _test_credentials(self, api_token: str) -> None:
    """Validate credentials."""
    client = SynciIntegrationApiClient(
      api_token=api_token,
      session=async_get_clientsession(self.hass),
    )
    await client.async_get_user_data()
