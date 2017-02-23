"""Test dispatcher helpers."""
import asyncio

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import (
    dispatcher_send, dispatcher_connect)

from tests.common import get_test_home_assistant


class TestHelpersDispatcher(object):
    """Tests for discovery helper methods."""

    def setup_method(self, method):
        """Setup things to be run when tests are started."""
        self.hass = get_test_home_assistant()

    def teardown_method(self, method):
        """Stop everything that was started."""
        self.hass.stop()

    def test_simple_function(self):
        """Test simple function (executor)."""
        calls = []

        def test_funct(data):
            """Test function."""
            calls.append(data)

        dispatcher_connect(self.hass, 'test', test_funct)
        self.hass.block_till_done()

        dispatcher_send(self.hass, 'test', 3)
        self.hass.block_till_done()

        assert calls == [3]

        dispatcher_send(self.hass, 'test', 'bla')
        self.hass.block_till_done()

        assert calls == [3, 'bla']

    def test_simple_callback(self):
        """Test simple callback (async)."""
        calls = []

        @callback
        def test_funct(data):
            """Test function."""
            calls.append(data)

        dispatcher_connect(self.hass, 'test', test_funct)
        self.hass.block_till_done()

        dispatcher_send(self.hass, 'test', 3)
        self.hass.block_till_done()

        assert calls == [3]

        dispatcher_send(self.hass, 'test', 'bla')
        self.hass.block_till_done()

        assert calls == [3, 'bla']

    def test_simple_coro(self):
        """Test simple coro (async)."""
        calls = []

        @asyncio.coroutine
        def test_funct(data):
            """Test function."""
            calls.append(data)

        dispatcher_connect(self.hass, 'test', test_funct)
        self.hass.block_till_done()

        dispatcher_send(self.hass, 'test', 3)
        self.hass.block_till_done()

        assert calls == [3]

        dispatcher_send(self.hass, 'test', 'bla')
        self.hass.block_till_done()

        assert calls == [3, 'bla']

    def test_simple_function_multiargs(self):
        """Test simple function (executor)."""
        calls = []

        def test_funct(data1, data2, data3):
            """Test function."""
            calls.append(data1)
            calls.append(data2)
            calls.append(data3)

        dispatcher_connect(self.hass, 'test', test_funct)
        self.hass.block_till_done()

        dispatcher_send(self.hass, 'test', 3, 2, 'bla')
        self.hass.block_till_done()

        assert calls == [3, 2, 'bla']
