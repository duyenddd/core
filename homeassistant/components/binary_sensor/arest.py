"""
homeassistant.components.binary_sensor.arest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The arest sensor will consume an exposed aREST API of a device.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.arest/
"""
from datetime import timedelta
import logging

import requests

from homeassistant.util import Throttle
from homeassistant.components.binary_sensor import BinarySensorDevice

_LOGGER = logging.getLogger(__name__)

# Return cached results if last scan was less then this time ago
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

CONF_RESOURCE = 'resource'
CONF_PIN = 'pin'


def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Get the aREST binary sensor. """

    resource = config.get(CONF_RESOURCE)
    pin = config.get(CONF_PIN)

    if None in (resource, pin):
        _LOGGER.error('Not all required config keys present: %s',
                      ', '.join((CONF_RESOURCE, CONF_PIN)))
        return False

    try:
        response = requests.get(resource, timeout=10).json()
    except requests.exceptions.MissingSchema:
        _LOGGER.error('Missing resource or schema in configuration. '
                      'Add http:// to your URL.')
        return False
    except requests.exceptions.ConnectionError:
        _LOGGER.error('No route to device at %s. '
                      'Please check the IP address in the configuration file.',
                      resource)
        return False

    arest = ArestData(resource, pin)

    add_devices([ArestBinarySensor(arest,
                                   resource,
                                   config.get('name', response['name']),
                                   pin)])


# pylint: disable=too-many-instance-attributes, too-many-arguments
class ArestBinarySensor(BinarySensorDevice):
    """ Implements an aREST binary sensor for a pin. """

    def __init__(self, arest, resource, name, pin):
        self.arest = arest
        self._resource = resource
        self._name = name
        self._pin = pin
        self.update()

        if self._pin is not None:
            request = requests.get('{}/mode/{}/i'.format
                                   (self._resource, self._pin), timeout=10)
            if request.status_code is not 200:
                _LOGGER.error("Can't set mode. Is device offline?")

    @property
    def name(self):
        """ The name of the binary sensor. """
        return self._name

    @property
    def is_on(self):
        """ True if the binary sensor is on. """
        return bool(self.arest.data.get('state'))

    def update(self):
        """ Gets the latest data from aREST API. """
        self.arest.update()


# pylint: disable=too-few-public-methods
class ArestData(object):
    """ Class for handling the data retrieval for pins. """

    def __init__(self, resource, pin):
        self._resource = resource
        self._pin = pin
        self.data = {}

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """ Gets the latest data from aREST device. """
        try:
            response = requests.get('{}/digital/{}'.format(
                self._resource, self._pin), timeout=10)
            self.data = {'state': response.json()['return_value']}
        except requests.exceptions.ConnectionError:
            _LOGGER.error("No route to device '%s'. Is device offline?",
                          self._resource)
