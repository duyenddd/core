"""Test script variables."""
import pytest

from homeassistant.helpers import config_validation as cv, template


async def test_static_vars():
    """Test static vars."""
    orig = {"hello": "world"}
    var = cv.SCRIPT_VARIABLES_SCHEMA(orig)
    rendered = var.async_render(None, None)
    assert rendered is not orig
    assert rendered == orig


async def test_static_vars_run_args():
    """Test static vars."""
    orig = {"hello": "world"}
    orig_copy = dict(orig)
    var = cv.SCRIPT_VARIABLES_SCHEMA(orig)
    rendered = var.async_render(None, {"hello": "override", "run": "var"})
    assert rendered == {"hello": "override", "run": "var"}
    # Make sure we don't change original vars
    assert orig == orig_copy


async def test_template_vars(hass):
    """Test template vars."""
    var = cv.SCRIPT_VARIABLES_SCHEMA({"hello": "{{ 1 + 1 }}"})
    rendered = var.async_render(hass, None)
    assert rendered == {"hello": "2"}


async def test_template_vars_run_args(hass):
    """Test template vars."""
    var = cv.SCRIPT_VARIABLES_SCHEMA(
        {
            "something": "{{ run_var_ex + 1 }}",
            "something_2": "{{ run_var_ex + 1 }}",
        }
    )
    rendered = var.async_render(
        hass,
        {
            "run_var_ex": 5,
            "something_2": 1,
        },
    )
    assert rendered == {
        "run_var_ex": 5,
        "something": "6",
        "something_2": 1,
    }


async def test_template_vars_error(hass):
    """Test template vars."""
    var = cv.SCRIPT_VARIABLES_SCHEMA({"hello": "{{ canont.work }}"})
    with pytest.raises(template.TemplateError):
        var.async_render(hass, None)
