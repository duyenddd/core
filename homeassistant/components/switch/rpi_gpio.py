"""
homeassistant.components.switch.rpi_gpio
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Allows to control a swith using Raspberry GPIO.
Support for switching Raspberry GPIO pins on and off.

Configuration:

switch:
  platform: rpi_gpio
  ports:
    11: Fan Office
    12: Light Desk

Variables:

ports
*Required
An array specifying the GPIO ports to use and the name usd in the fronted.

"""
import logging
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.const import (DEVICE_DEFAULT_NAME,
                                 EVENT_HOMEASSISTANT_START,
                                 EVENT_HOMEASSISTANT_STOP)

REQUIREMENTS = ['RPi.GPIO>=0.5.11']
_LOGGER = logging.getLogger(__name__)


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Sets up the Raspberry PI GPIO switches. """
    if GPIO is None:
        _LOGGER.error('RPi.GPIO not available. rpi_gpio switches ignored.')
        return

    switches = []
    ports = config.get('ports')
    for port_num, port_name in ports.items():
        switches.append(RPiGPIOSwitch(port_name, port_num))
    add_devices(switches)

    def cleanup_gpio(event):
        """ Stop the Arduino service. """
        GPIO.cleanup()

    def prepare_gpio(event):
        """ Start the Arduino service. """
        hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, cleanup_gpio)

    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, prepare_gpio)


class RPiGPIOSwitch(ToggleEntity):

    '''
    Represents a switch that can be toggled using Raspberry Pi GPIO.
    '''

    def __init__(self, name, gpio):
        self._name = name or DEVICE_DEFAULT_NAME
        self._state = False
        self._gpio = gpio
        GPIO.setup(gpio, GPIO.OUT)

    @property
    def name(self):
        """ The name of the port """
        return self._name

    @property
    def should_poll(self):
        """ No polling needed """
        return False

    @property
    def is_on(self):
        """ True if device is on. """
        return self._state

    def turn_on(self, **kwargs):
        """ Turn the device on. """
        if self._switch(True):
            self._state = True
        self.update_ha_state()

    def turn_off(self, **kwargs):
        """ Turn the device off. """
        if self._switch(False):
            self._state = False
        self.update_ha_state()

    def _switch(self, new_state):
        """ Execute the actual commands """
        _LOGGER.info('Setting GPIO %s to %s', self._gpio, new_state)
        try:
            GPIO.output(self._gpio, 1 if new_state else 0)
        except:
            _LOGGER.error('GPIO "%s" output failed', self._gpio)
            return False
        return True

    @property
    def device_state_attributes(self):
        """ Returns device specific state attributes. """
        return None

    @property
    def state_attributes(self):
        """ Returns optional state attributes. """
        data = {}
        device_attr = self.device_state_attributes
        if device_attr is not None:
            data.update(device_attr)
        return data
