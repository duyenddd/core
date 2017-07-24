"""
Support for tracking a Volvo.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.volvooncall/
"""
import logging

from homeassistant.util import slugify
from homeassistant.helpers.dispatcher import (
    dispatcher_connect, dispatcher_send)
from homeassistant.components.volvooncall import DATA_KEY, SIGNAL_VEHICLE_SEEN

_LOGGER = logging.getLogger(__name__)


def setup_scanner(hass, config, see, discovery_info=None):
    """Set up the Volvo tracker."""
    if discovery_info is None:
        return

    vin, _ = discovery_info
    vehicle = hass.data[DATA_KEY].vehicles[vin]

    def see_vehicle(vehicle):
        """Handle the reporting of the vehicle position."""
        host_name = vehicle.registration_number
        dev_id = 'volvo_{}'.format(slugify(host_name))
        see(dev_id=dev_id,
            host_name=host_name,
            gps=(vehicle.position['latitude'],
                 vehicle.position['longitude']),
            icon='mdi:car')

    dispatcher_connect(hass, SIGNAL_VEHICLE_SEEN, see_vehicle)
    dispatcher_send(hass, SIGNAL_VEHICLE_SEEN, vehicle)

    return True
