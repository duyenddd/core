"""Test the Sonarr config flow."""
from unittest.mock import MagicMock, patch

from sonarr import SonarrAccessRestricted, SonarrError

from homeassistant.components.sonarr.const import (
    CONF_UPCOMING_DAYS,
    CONF_WANTED_MAX_ITEMS,
    DEFAULT_UPCOMING_DAYS,
    DEFAULT_WANTED_MAX_ITEMS,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_SOURCE, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from tests.common import MockConfigEntry
from tests.components.sonarr import MOCK_REAUTH_INPUT, MOCK_USER_INPUT


async def test_show_user_form(hass: HomeAssistant) -> None:
    """Test that the user set up form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    assert result["step_id"] == "user"
    assert result["type"] == RESULT_TYPE_FORM


async def test_cannot_connect(
    hass: HomeAssistant, mock_sonarr_config_flow: MagicMock
) -> None:
    """Test we show user form on connection error."""
    mock_sonarr_config_flow.update.side_effect = SonarrError

    user_input = MOCK_USER_INPUT.copy()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_invalid_auth(
    hass: HomeAssistant, mock_sonarr_config_flow: MagicMock
) -> None:
    """Test we show user form on invalid auth."""
    mock_sonarr_config_flow.update.side_effect = SonarrAccessRestricted

    user_input = MOCK_USER_INPUT.copy()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_unknown_error(
    hass: HomeAssistant, mock_sonarr_config_flow: MagicMock
) -> None:
    """Test we show user form on unknown error."""
    mock_sonarr_config_flow.update.side_effect = Exception

    user_input = MOCK_USER_INPUT.copy()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "unknown"


async def test_full_reauth_flow_implementation(
    hass: HomeAssistant,
    mock_sonarr_config_flow: MagicMock,
    mock_setup_entry: None,
    init_integration: MockConfigEntry,
) -> None:
    """Test the manual reauth flow from start to finish."""
    entry = init_integration

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            CONF_SOURCE: SOURCE_REAUTH,
            "entry_id": entry.entry_id,
            "unique_id": entry.unique_id,
        },
        data=entry.data,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    user_input = MOCK_REAUTH_INPUT.copy()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )
    await hass.async_block_till_done()

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "reauth_successful"

    assert entry.data[CONF_API_KEY] == "test-api-key-reauth"


async def test_full_user_flow_implementation(
    hass: HomeAssistant,
    mock_sonarr_config_flow: MagicMock,
    mock_setup_entry: None,
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    user_input = MOCK_USER_INPUT.copy()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input,
    )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "192.168.1.189"

    assert result["data"]
    assert result["data"][CONF_HOST] == "192.168.1.189"


async def test_full_user_flow_advanced_options(
    hass: HomeAssistant,
    mock_sonarr_config_flow: MagicMock,
    mock_setup_entry: None,
) -> None:
    """Test the full manual user flow with advanced options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER, "show_advanced_options": True}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    user_input = {
        **MOCK_USER_INPUT,
        CONF_VERIFY_SSL: True,
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input,
    )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "192.168.1.189"

    assert result["data"]
    assert result["data"][CONF_HOST] == "192.168.1.189"
    assert result["data"][CONF_VERIFY_SSL]


@patch("homeassistant.components.sonarr.PLATFORMS", [])
async def test_options_flow(
    hass: HomeAssistant,
    mock_setup_entry: None,
    init_integration: MockConfigEntry,
):
    """Test updating options."""
    entry = init_integration

    assert entry.options[CONF_UPCOMING_DAYS] == DEFAULT_UPCOMING_DAYS
    assert entry.options[CONF_WANTED_MAX_ITEMS] == DEFAULT_WANTED_MAX_ITEMS

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_UPCOMING_DAYS: 2, CONF_WANTED_MAX_ITEMS: 100},
    )
    await hass.async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["data"][CONF_UPCOMING_DAYS] == 2
    assert result["data"][CONF_WANTED_MAX_ITEMS] == 100
