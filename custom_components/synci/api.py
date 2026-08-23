from __future__ import annotations

import asyncio
import math
import socket
from contextlib import suppress
from http import HTTPStatus
from typing import Any

import aiohttp


class SynciIntegrationApiClientError(Exception):
  """Exception to indicate a general API error."""


class SynciIntegrationApiClientCommunicationError(
  SynciIntegrationApiClientError,
):
  """Exception to indicate a communication error."""


class SynciIntegrationApiClientAuthenticationError(
  SynciIntegrationApiClientError,
):
  """Exception to indicate an authentication error."""


class SynciIntegrationApiClientRateLimitError(
  SynciIntegrationApiClientCommunicationError,
):
  """Exception to indicate the API is rate limiting us."""

  def __init__(self, message: str, retry_after: int | None = None) -> None:
    """Store the backoff period requested by the API."""
    super().__init__(message)
    self.retry_after = retry_after


def _parse_retry_after(response: aiohttp.ClientResponse) -> int:
  """Return the backoff period (whole seconds) from the Retry-After header."""
  value: float | None = None
  retry_after = response.headers.get("Retry-After")
  if retry_after is not None:
    with suppress(ValueError):
      value = float(retry_after)
  if value is not None and math.isfinite(value) and value >= 0:
    return math.ceil(value)
  return 60


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
  """Verify that the response is valid."""
  if response.status in (401, 403):
    msg = "Invalid credentials"
    raise SynciIntegrationApiClientAuthenticationError(
      msg,
    )
  if response.status == HTTPStatus.TOO_MANY_REQUESTS:
    msg = "Rate limited by the API"
    raise SynciIntegrationApiClientRateLimitError(
      msg,
      retry_after=_parse_retry_after(response),
    )
  response.raise_for_status()


class SynciIntegrationApiClient:
  """Sample API Client."""

  def __init__(
    self,
    api_token: str,
    session: aiohttp.ClientSession,
  ) -> None:
    """Sample API Client."""
    self._api_token = api_token
    self._session = session

  async def async_get_data(self) -> Any:
    """Get data from the API."""
    return (await self._api_wrapper(
      method="get",
      url="https://api.synci.io/api/v1/finance/connections",
    ))["data"]

  async def async_get_connection_data(self, id) -> Any:
    """Get data from the API."""
    return (await self._api_wrapper(
      method="get",
      url=f"https://api.synci.io/api/v1/finance/connections/{id}",
    ))["data"]

  async def async_get_user_data(self) -> Any:
    return (await self._api_wrapper(
      method="get",
      url="https://api.synci.io/api/v1/user",
    ))["data"]

  async def _api_wrapper(
    self,
    method: str,
    url: str,
    data: dict | None = None,
    headers: dict | None = None,
  ) -> Any:
    """Get information from the API."""
    try:
      async with asyncio.timeout(10):
        response = await self._session.request(
          method=method,
          url=url,
          headers= {
            'Authorization': "Bearer " + self._api_token,
          },
          json=data,
        )
        _verify_response_or_raise(response)
        return await response.json()

    except TimeoutError as exception:
      msg = f"Timeout error fetching information - {exception}"
      raise SynciIntegrationApiClientCommunicationError(
        msg,
      ) from exception
    except (aiohttp.ClientError, socket.gaierror) as exception:
      msg = f"Error fetching information - {exception}"
      raise SynciIntegrationApiClientCommunicationError(
        msg,
      ) from exception
    except SynciIntegrationApiClientError:
      # Our own typed errors (auth, rate-limit, communication) are already
      # meaningful; re-raise so callers can branch on them instead of masking
      # them with the broad handler below.
      raise
    except Exception as exception:  # pylint: disable=broad-except
      msg = f"Something really wrong happened! - {exception}"
      raise SynciIntegrationApiClientError(
        msg,
      ) from exception
