#!/usr/bin/env python
"""Class to keep information of one property."""

from dateutil.parser import parse

# We really only have little public methods
# pylint: disable=R0903


class OwletProperty():
    """Class to keep information of one property."""

    def __init__(self, json):
        """Initialize property from json object as argument."""
        self.name = None
        self.display_name = None
        self.value = None
        self.last_update = None
        self.minimum_update_interval = None
        self.key = None
        self.type = None
        self.base_type = None
        self.read_only = None
        self.direction = None
        self.scope = None
        self.data_updated_at = None
        self.device_key = None
        self.product_name = None
        self.track_only_changes = None
        self.host_sw_version = None
        self.time_series = None
        self.derived = None
        self.app_type = None
        self.recipe = None
        self.generated_from = None
        self.generated_at = None
        self.denied_roles = None
        self.ack_enabled = None
        self.retention_days = None
        self.ack_status = None
        self.ack_message = None
        self.acked_at = None

        self._from_json(json)

    def update(self, json):
        """Update property from JSON."""
        self._from_json(json)

    def _from_json(self, json):
        """Parse JSON and update attributes of class."""
        self.name = json['name'] if 'name' in json else ''
        self.display_name = json['display_name'] if 'display_name' in json else ''
        self.value = json['value'] if 'value' in json else ''
        self.key = json['key'] if 'key' in json else ''
        self.type = json['type'] if 'type' in json else ''
        self.base_type = json['base_type'] if 'base_type' in json else ''
        self.read_only = json['read_only'] if 'read_only' in json else ''
        self.direction = json['direction'] if 'direction' in json else ''
        self.scope = json['scope'] if 'scope' in json else ''
        self.data_updated_at = json['data_updated_at'] if 'data_updated_at' in json else ''
        self.device_key = json['device_key'] if 'device_key' in json else ''
        self.product_name = json['product_name'] if 'product_name' in json else ''
        self.track_only_changes = json['track_only_changes'] if 'track_only_changes' in json else ''
        self.host_sw_version = json['host_sw_version'] if 'host_sw_version' in json else ''
        self.time_series = json['time_series'] if 'time_series' in json else ''
        self.derived = json['derived'] if 'derived' in json else ''
        self.app_type = json['app_type'] if 'app_type' in json else ''
        self.recipe = json['recipe'] if 'recipe' in json else ''
        self.generated_from = json['generated_from'] if 'generated_from' in json else ''
        self.generated_at = json['generated_at'] if 'generated_at' in json else ''
        self.denied_roles = json['denied_roles'] if 'denied_roles' in json else ''
        self.ack_enabled = json['ack_enabled'] if 'ack_enabled' in json else ''
        self.retention_days = json['retention_days'] if 'retention_days' in json else ''
        self.ack_status = json['ack_status'] if 'ack_status' in json else ''
        self.ack_message = json['ack_message'] if 'ack_message' in json else ''
        self.acked_at = json['acked_at'] if 'acked_at' in json else ''

        if json['data_updated_at'] != "null":
            new_update = parse(json['data_updated_at'])

            if self.last_update is not None and \
               new_update != self.last_update:
                update_interval = new_update - self.last_update

                if self.minimum_update_interval is None or \
                   update_interval.seconds < self.minimum_update_interval:
                    self.minimum_update_interval = update_interval.seconds

            self.last_update = new_update
