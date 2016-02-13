"""
homeassistant.components.scsgate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Provides support for SCSGate components.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/scsgate/
"""
import logging
from threading import Lock
from homeassistant.core import EVENT_HOMEASSISTANT_STOP

REQUIREMENTS = ['scsgate==0.1.0']
DOMAIN = "scsgate"
SCSGATE = None
_LOGGER = logging.getLogger(__name__)


class SCSGate:
    """ Class dealing with the SCSGate device via scsgate.Reactor. """

    def __init__(self, device, logger):
        self._logger = logger
        self._devices = {}
        self._devices_to_register = {}
        self._devices_to_register_lock = Lock()
        self._device_being_registered = None
        self._device_being_registered_lock = Lock()

        from scsgate.connection import Connection
        connection = Connection(device=device, logger=self._logger)

        from scsgate.reactor import Reactor
        self._reactor = Reactor(
            connection=connection,
            logger=self._logger,
            handle_message=self.handle_message)

    def handle_message(self, message):
        """ Method called whenever a message is seen on the bus. """
        from scsgate.messages import StateMessage, ScenarioTriggeredMessage

        self._logger.debug("Received message {}".format(message))
        if not isinstance(message, StateMessage) and \
           not isinstance(message, ScenarioTriggeredMessage):
            msg = "Ignored message {} - not releavant type".format(
                message)
            self._logger.debug(msg)
            return

        if message.entity in self._devices:
            new_device_activated = False
            with self._devices_to_register_lock:
                if message.entity == self._device_being_registered:
                    self._device_being_registered = None
                    new_device_activated = True
            if new_device_activated:
                self._activate_next_device()

            # pylint: disable=broad-except
            try:
                self._devices[message.entity].process_event(message)
            except Exception as exception:
                msg = "Exception while processing event: {}".format(
                    exception)
                self._logger.error(msg)
        else:
            self._logger.info(
                "Ignoring state message for device {} because unknonw".format(
                    message.entity))

    @property
    def devices(self):
        """
        Dictionary with known devices. Key is device ID, value is the device
        itself.
        """
        return self._devices

    def add_device(self, device):
        """
        Adds the specified device to the list of the already registered ones.

        Beware: this is not what you usually want to do, take a look at
        `add_devices_to_register`
        """
        self._devices[device.scs_id] = device

    def add_devices_to_register(self, devices):
        """ List of devices to be registered. """
        with self._devices_to_register_lock:
            for device in devices:
                self._devices_to_register[device.scs_id] = device
        self._activate_next_device()

    def _activate_next_device(self):
        """ Starts the activation of the first device. """
        from scsgate.tasks import GetStatusTask

        with self._devices_to_register_lock:
            if len(self._devices_to_register) == 0:
                return
            _, device = self._devices_to_register.popitem()
            self._devices[device.scs_id] = device
            self._device_being_registered = device.scs_id
            self._reactor.append_task(GetStatusTask(target=device.scs_id))

    def is_device_registered(self, device_id):
        """ Checks whether a device is already registered or not. """
        with self._devices_to_register_lock:
            if device_id in self._devices_to_register.keys():
                return False

        with self._device_being_registered_lock:
            if device_id == self._device_being_registered:
                return False

        return True

    def start(self):
        """ Start the scsgate.Reactor. """
        self._reactor.start()

    def stop(self):
        """ Stop the scsgate.Reactor. """
        self._reactor.stop()

    def append_task(self, task):
        """ Registers a new task to be executed. """
        self._reactor.append_task(task)


def setup(hass, config):
    """ Setup the SCSGate component. """
    device = config['scsgate']['device']
    global SCSGATE

    # pylint: disable=broad-except
    try:
        SCSGATE = SCSGate(device=device, logger=_LOGGER)
        SCSGATE.start()
    except Exception as exception:
        _LOGGER.error("Cannot setup SCSGate component: %s", exception)
        return False

    def stop_monitor(event):
        """
        Invoked when home-assistant is exiting. Performs the necessary
        cleanups.
        """
        _LOGGER.info("Stopping SCSGate monitor thread")
        SCSGATE.stop()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, stop_monitor)

    return True
