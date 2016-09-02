"""
Instapush notification service.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/notify.instapush/
"""
import json
import logging

import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.notify import (
    ATTR_TITLE, ATTR_TITLE_DEFAULT, PLATFORM_SCHEMA, BaseNotificationService)
from homeassistant.const import CONF_API_KEY


CONF_APP_SECRET = 'app_secret'
CONF_EVENT = 'event'
CONF_TRACKER = 'tracker'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_APP_SECRET): cv.string,
    vol.Required(CONF_EVENT): cv.string,
    vol.Required(CONF_TRACKER): cv.string,
})


_LOGGER = logging.getLogger(__name__)
_RESOURCE = 'https://api.instapush.im/v1/'


def get_service(hass, config):
    """Get the instapush notification service."""
    headers = {'x-instapush-appid': config[CONF_API_KEY],
               'x-instapush-appsecret': config[CONF_APP_SECRET]}

    try:
        response = requests.get(_RESOURCE + 'events/list',
                                headers=headers).json()
    except ValueError:
        _LOGGER.error('Unexpected answer from Instapush API.')
        return None

    if 'error' in response:
        _LOGGER.error(response['msg'])
        return None

    if len([app for app in response
            if app['title'] == config[CONF_EVENT]]) == 0:
        _LOGGER.error(
            "No app match your given value. "
            "Please create an app at https://instapush.im")
        return None

    return InstapushNotificationService(
        config[CONF_API_KEY], config[CONF_APP_SECRET], config[CONF_EVENT],
        config[CONF_TRACKER])


# pylint: disable=too-few-public-methods
class InstapushNotificationService(BaseNotificationService):
    """Implement the notification service for Instapush."""

    def __init__(self, api_key, app_secret, event, tracker):
        """Initialize the service."""
        self._api_key = api_key
        self._app_secret = app_secret
        self._event = event
        self._tracker = tracker
        self._headers = {
            'x-instapush-appid': self._api_key,
            'x-instapush-appsecret': self._app_secret,
            'Content-Type': 'application/json'}

    def send_message(self, message="", **kwargs):
        """Send a message to a user."""
        title = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)
        data = {"event": self._event,
                "trackers": {self._tracker: title + " : " + message}}

        response = requests.post(_RESOURCE + 'post', data=json.dumps(data),
                                 headers=self._headers)

        if response.json()['status'] == 401:
            _LOGGER.error(
                response.json()['msg'],
                "Please check your details at https://instapush.im/")
