"""
homeassistant.components.sensor.rfxtrx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shows sensor values from RFXtrx sensors.

Configuration:

To use the rfxtrx sensors you will need to add something like the following to
your configuration.yaml file.

sensor:
    platform: rfxtrx
    device: PATH_TO_DEVICE

Variables:

device
*Required
Path to your RFXtrx device.
E.g. /dev/serial/by-id/usb-RFXCOM_RFXtrx433_A1Y0NJGR-if00-port0
"""
import logging
from collections import OrderedDict

from homeassistant.const import (TEMP_CELCIUS)
from homeassistant.helpers.entity import Entity
import homeassistant.components.rfxtrx as rfxtrx
from RFXtrx import SensorEvent
from homeassistant.util import slugify

REQUIREMENTS = ['https://github.com/Danielhiversen/pyRFXtrx/archive/' +
                'ec7a1aaddf8270db6e5da1c13d58c1547effd7cf.zip#RFXtrx==0.15']

DATA_TYPES = OrderedDict([
    ('Temperature', TEMP_CELCIUS),
    ('Humidity', '%'),
    ('Barometer', ''),
    ('Wind direction', ''),
    ('Rain rate', '')])


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """ Setup the RFXtrx platform. """
    logger = logging.getLogger(__name__)

    sensors = {}    # keep track of sensors added to HA

    def sensor_update(event):
        """ Callback for sensor updates from the RFXtrx gateway. """
        if isinstance(event.device, SensorEvent):
            entity_id = '%s-%s' % (event.device.type_string.lower(), slugify(event.device.id_string.lower()))
            if entity_id in rfxtrx.RFX_DEVICES:
                rfxtrx.RFX_DEVICES[entity_id].event = event
            else:
                automatic_add = config.get('automatic_add', False)
                if automatic_add:
                    new_light = RfxtrxSensor(entity_id, False)
                    rfxtrx.RFX_DEVICES[entity_id] = new_light
                    add_devices_callback([new_light])

    if sensor_update not in rfxtrx.RECEIVED_EVT_SUBSCRIBERS:
        rfxtrx.RECEIVED_EVT_SUBSCRIBERS.append(sensor_update)

class RfxtrxSensor(Entity):
    """ Represents a RFXtrx sensor. """

    def __init__(self, event):
        self.event = event

        self._unit_of_measurement = None
        self._data_type = None
        for data_type in DATA_TYPES:
            if data_type in self.event.values:
                self._unit_of_measurement = DATA_TYPES[data_type]
                self._data_type = data_type
                break

        id_string = int(event.device.id_string.replace(":", ""), 16)
        self._name = "{} {} ({})".format(self._data_type,
                                         self.event.device.type_string,
                                         id_string)

    def __str__(self):
        return self._name

    @property
    def state(self):
        if self._data_type:
            return self.event.values[self._data_type]
        return None

    @property
    def name(self):
        """ Get the mame of the sensor. """
        return self._name

    @property
    def state_attributes(self):
        return self.event.values

    @property
    def unit_of_measurement(self):
        """ Unit this state is expressed in. """
        return self._unit_of_measurement
