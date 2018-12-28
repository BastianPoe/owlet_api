#!/usr/bin/env python
"""Command Line Interface for OwletAPI."""

import argparse
import time
import sys
from owlet_api.owletapi import OwletAPI
from owlet_api.owletexceptions import OwletTemporaryCommunicationException
from owlet_api.owletexceptions import OwletPermanentCommunicationException


# By nature, a single command line interface function will trigger some of
# pylints checks
# pylint: disable=R0912,R0915,R1702
def cli():
    """Command Line Interface for Owletapi."""
    parser = argparse.ArgumentParser(
        description='Owlet API Command Line Interface')
    parser.add_argument('email', help='Specify Email Address')
    parser.add_argument('password', help='Specify Password')
    parser.add_argument('actions', help='Specify the actions', nargs='+',
                        choices=["token", "devices", "attributes",
                                 "stream", 'download'])
    parser.add_argument('--device', dest='device',
                        help='Specify DSN for device filter')
    parser.add_argument('--stream', dest='attributes', action='append',
                        help='Specify attributes for stream filter')
    parser.add_argument('--timeout', dest='timeout',
                        help='Specify streaming timeout in seconds')
    # Parse arguments
    args = parser.parse_args()

    if args.timeout:
        timeout = time.time() + float(args.timeout)
    else:
        timeout = None

    # Initialize Owlet api
    api = OwletAPI()

    # Provide Login data
    api.set_email(args.email)
    api.set_password(args.password)

    # Login
    try:
        api.login()
    except OwletPermanentCommunicationException:
        print("Login failed, username or passwort might be wrong")
        sys.exit(1)
    except OwletTemporaryCommunicationException:
        print("Login failed, server might be down")
        sys.exit(1)

    # Print token
    if "token" in args.actions:
        print("Token: %s" % api.get_auth_token())

    # print Devices
    if "devices" in args.actions:
        for device in api.get_devices():
            if args.device is None or args.device == device.dsn:
                print("%15s %-7s %2.4f %2.4f" %
                      (device.dsn, device.connection_status,
                       device.lat, device.lon))

    # print Attributes
    if "attributes" in args.actions:
        for device in api.get_devices():
            if args.device is None or args.device == device.dsn:
                device.update()
                for name, myproperty in device.get_properties().items():
                    print("%-19s %-21s %-20s %s" %
                          (myproperty.name, myproperty.display_name,
                           myproperty.last_update, myproperty.value))

    if "download" in args.actions:
        for device in api.get_devices():
            if args.device is None or args.device == device.dsn:
                device.update()
                print(device.download_logged_data())

    # Stream Attributes
    if "stream" in args.actions:
        # If no attributes for streaming have been defined, we stream
        # everything
        if args.attributes is None:
            args.attributes = []
            for device in api.get_devices():
                if args.device is None or args.device == device.dsn:
                    device.update()
                    for name, myproperty in device.get_properties().items():
                        args.attributes.append(name)

        # CSV header
        header = "TIMESTAMP;DSN;"
        for attribute in args.attributes:
            header = header + attribute + ";"
        print(header)

        # Stream forever
        while timeout is None or time.time() < timeout:
            start = time.time()

            for device in api.get_devices():
                try:
                    device.update()
                except OwletTemporaryCommunicationException:
                    continue

                try:
                    device.reactivate()
                except OwletTemporaryCommunicationException:
                    continue

                if args.device is None or args.device == device.dsn:
                    line = str(time.time()) + ";" + device.dsn + ";"
                    properties = device.get_properties()

                    for attribute in args.attributes:
                        if attribute in properties:
                            line = line + \
                                str(properties[attribute].value) + ";"

                    print(line)
                    sys.stdout.flush()

            wait_time = api.get_update_interval() - (time.time() - start)
            try:
                time.sleep(max(0, wait_time))
            except (KeyboardInterrupt, SystemExit):
                sys.exit(0)


def init():
    """Mandatory init function."""
    if __name__ == "__main__":
        sys.exit(cli())


init()
