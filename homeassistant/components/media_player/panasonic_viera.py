"""
Support for interface with a Panasonic Viera TV.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.panasonic_viera/
"""
import logging

import voluptuous as vol

from homeassistant.components.media_player import (
    SUPPORT_NEXT_TRACK, SUPPORT_PAUSE, SUPPORT_PREVIOUS_TRACK,
    SUPPORT_TURN_OFF, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP, MediaPlayerDevice, PLATFORM_SCHEMA)
from homeassistant.const import (
    CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_UNKNOWN, CONF_PORT)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['panasonic_viera==0.2']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Panasonic Viera TV'
DEFAULT_PORT = 55000

SUPPORT_VIERATV = SUPPORT_PAUSE | SUPPORT_VOLUME_STEP | \
    SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | \
    SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | \
    SUPPORT_TURN_OFF

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Panasonic Viera TV platform."""
    from panasonic_viera import RemoteControl

    name = config.get(CONF_NAME)
    port = config.get(CONF_PORT)

    if discovery_info:
        _LOGGER.debug('%s', discovery_info)
        vals = discovery_info.split(':')
        if len(vals) > 1:
            port = vals[1]

        host = vals[0]
        remote = RemoteControl(host, port)
        add_devices([PanasonicVieraTVDevice(name, remote)])
        return True

    host = config.get(CONF_HOST)
    remote = RemoteControl(host, port)

    try:
        remote.get_mute()
    except OSError as error:
        _LOGGER.error('Panasonic Viera TV is not available at %s:%d: %s',
                      host, port, error)
        return False

    add_devices([PanasonicVieraTVDevice(name, remote)])
    return True


# pylint: disable=abstract-method
class PanasonicVieraTVDevice(MediaPlayerDevice):
    """Representation of a Panasonic Viera TV."""

    def __init__(self, name, remote):
        """Initialize the Panasonic device."""
        # Save a reference to the imported class
        self._name = name
        self._muted = False
        self._playing = True
        self._state = STATE_UNKNOWN
        self._remote = remote

    def update(self):
        """Retrieve the latest data."""
        try:
            self._muted = self._remote.get_mute()
            self._state = STATE_ON
        except OSError:
            self._state = STATE_OFF
            return False
        return True

    def send_key(self, key):
        """Send a key to the tv and handles exceptions."""
        try:
            self._remote.send_key(key)
            self._state = STATE_ON
        except OSError:
            self._state = STATE_OFF
            return False
        return True

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        volume = 0
        try:
            volume = self._remote.get_volume() / 100
            self._state = STATE_ON
        except OSError:
            self._state = STATE_OFF
        return volume

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        return SUPPORT_VIERATV

    def turn_off(self):
        """Turn off media player."""
        self.send_key('NRC_POWER-ONOFF')

    def volume_up(self):
        """Volume up the media player."""
        self.send_key('NRC_VOLUP-ONOFF')

    def volume_down(self):
        """Volume down media player."""
        self.send_key('NRC_VOLDOWN-ONOFF')

    def mute_volume(self, mute):
        """Send mute command."""
        self.send_key('NRC_MUTE-ONOFF')

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        volume = int(volume * 100)
        try:
            self._remote.set_volume(volume)
            self._state = STATE_ON
        except OSError:
            self._state = STATE_OFF

    def media_play_pause(self):
        """Simulate play pause media player."""
        if self._playing:
            self.media_pause()
        else:
            self.media_play()

    def media_play(self):
        """Send play command."""
        self._playing = True
        self.send_key('NRC_PLAY-ONOFF')

    def media_pause(self):
        """Send media pause command to media player."""
        self._playing = False
        self.send_key('NRC_PAUSE-ONOFF')

    def media_next_track(self):
        """Send next track command."""
        self.send_key('NRC_FF-ONOFF')

    def media_previous_track(self):
        """Send the previous track command."""
        self.send_key('NRC_REW-ONOFF')
