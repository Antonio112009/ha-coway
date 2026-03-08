"""Tests for the Coway config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pycoway import AuthError, CowayError, PasswordExpired

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ha_coway.const import DOMAIN

from .conftest import MOCK_USER_INPUT


async def test_full_user_flow(
    hass: HomeAssistant,
    mock_coway_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test successful config flow from user input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_USER_INPUT["username"]
    assert result["data"] == MOCK_USER_INPUT
    mock_coway_client.login.assert_awaited_once()


async def test_flow_auth_error(
    hass: HomeAssistant,
    mock_coway_client: AsyncMock,
) -> None:
    """Test config flow with invalid credentials."""
    mock_coway_client.login.side_effect = AuthError("Invalid credentials")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_flow_password_expired(
    hass: HomeAssistant,
    mock_coway_client: AsyncMock,
) -> None:
    """Test config flow when password has expired."""
    mock_coway_client.login.side_effect = PasswordExpired("Password must be changed")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "password_expired"}


async def test_flow_connection_error(
    hass: HomeAssistant,
    mock_coway_client: AsyncMock,
) -> None:
    """Test config flow when connection fails."""
    mock_coway_client.login.side_effect = CowayError("Connection timeout")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_unknown_error(
    hass: HomeAssistant,
    mock_coway_client: AsyncMock,
) -> None:
    """Test config flow with unexpected exception."""
    mock_coway_client.login.side_effect = RuntimeError("Something unexpected")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_flow_duplicate_entry(
    hass: HomeAssistant,
    mock_coway_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test config flow aborts when account is already configured."""
    # Set up the first entry successfully
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Attempt to set up the same account again
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_flow_recovery_after_error(
    hass: HomeAssistant,
    mock_coway_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test that the user can retry after an error."""
    mock_coway_client.login.side_effect = AuthError("Bad password")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    # User fixes credentials, retry succeeds
    mock_coway_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_options_flow(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test the options flow for polling interval."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_USER_INPUT,
        options={"polling_interval": 60},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"polling_interval": 120},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"polling_interval": 120}
