#!/usr/bin/env python
"""Class to keep information of one property."""

from dateutil.parser import parse

# We really only have little public methods
# pylint: disable=R0903


class OwletPropertyDatapoint():
    """Class to keep information of one property datapoint."""

    def __init__(self, json):
        """Initialize property datapoint from json object as argument."""
        self.id = None
        self.updated_at = None
        self.created_at = None
        self.created_at_from_device = None
        self.echo = None
        self.metadata = None
        self.generated_at = None
        self.generated_from = None
        self.value = None
        self.acked_at = None
        self.ack_status = None
        self.ack_message = None

        self._from_json(json)

    def update(self, json):
        """Update property datapoint from JSON."""
        self._from_json(json)

    def _from_json(self, json):
        """Parse JSON and update attributes of class."""
        self.id = json['id'] if 'id' in json else ''
        self.updated_at = json['updated_at'] if 'updated_at' in json else ''
        self.created_at = json['created_at'] if 'created_at' in json else ''
        self.created_at_from_device = json['created_at_from_device'] if 'created_at_from_device' in json else ''
        self.echo = json['echo'] if 'echo' in json else ''
        self.metadata = json['metadata'] if 'metadata' in json else ''
        self.generated_at = json['generated_at'] if 'generated_at' in json else ''
        self.generated_from = json['generated_from'] if 'generated_from' in json else ''
        self.value = json['value'] if 'value' in json else ''
        self.acked_at = json['acked_at'] if 'acked_at' in json else ''
        self.ack_status = json['ack_status'] if 'ack_status' in json else ''
        self.ack_message = json['ack_message'] if 'ack_message' in json else ''
