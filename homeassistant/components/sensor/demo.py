""" Support for Wink sensors. """
from homeassistant.helpers import Device
from homeassistant.const import (
    TEMP_CELCIUS, ATTR_UNIT_OF_MEASUREMENT, ATTR_FRIENDLY_NAME)


def get_devices(hass, config):
    """ Find and return Wink sensors. """

    return get_sensors()


def devices_discovered(hass, config, info):
    """ Called when a device is discovered. """
    return get_sensors()


def get_sensors():
    """ Returns the Wink sensors. """
    return [
        DemoSensor('Outside Temperature', 15.6, TEMP_CELCIUS),
        DemoSensor('Outside Humidity', 54, '%'),
    ]


class DemoSensor(Device):
    """ A Demo sensor. """

    def __init__(self, name, state, unit_of_measurement):
        self._name = name
        self._state = state
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self):
        """ Returns the name of the device. """
        return self._name

    @property
    def state(self):
        """ Returns the state of the device. """
        return self._state

    @property
    def state_attributes(self):
        """ Returns the state attributes. """
        return {
            ATTR_FRIENDLY_NAME: self._name,
            ATTR_UNIT_OF_MEASUREMENT: self._unit_of_measurement,
        }
