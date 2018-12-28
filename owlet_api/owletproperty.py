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

        self._from_json(json)

    def update(self, json):
        """Update property from JSON."""
        self._from_json(json)

    def _from_json(self, json):
        """Parse JSON and update attributes of class."""
        self.name = json['name']
        self.display_name = json['display_name']
        self.value = json['value']
        self.key = json['key']

        if json['data_updated_at'] != "null":
            new_update = parse(json['data_updated_at'])

            if self.last_update is not None and \
               new_update != self.last_update:
                update_interval = new_update - self.last_update

                if self.minimum_update_interval is None or \
                   update_interval.seconds < self.minimum_update_interval:
                    self.minimum_update_interval = update_interval.seconds

            self.last_update = new_update
