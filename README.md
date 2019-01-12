# Unofficial Python API for the Owlet Smart Baby Monitor 
[![Build Status](https://travis-ci.org/BastianPoe/owlet_api.svg?branch=master)](https://travis-ci.org/BastianPoe/owlet_api) [![Coverage Status](https://coveralls.io/repos/github/BastianPoe/owlet_api/badge.svg?branch=master)](https://coveralls.io/github/BastianPoe/owlet_api?branch=master)

This is an unofficial python API for retrieving data from the [Owlet Smart Sock](https://www.owletcare.com). The Owlet Smart Sock is a baby monitoring system that tries to prevent the [Sudden infant death syndrome](https://en.wikipedia.org/wiki/Sudden_infant_death_syndrome) by monitoring the baby's heartbeat as well as blood oxygen level via pulse oximetry and warning parents if abnormalities are detected.

The Owlet Smart Sock sends data to the [Ayla Networks](https://www.aylanetworks.com) cloud service. You can access it via the [Ayla API](https://developer.aylanetworks.com/apibrowser/). The meaning of many attributes is not yet known (to me), but some are more obvious. See here for an example:

```
TIMESTAMP;DSN;AGE_MONTHS_OLD;ALRTS_DISABLED;ALRT_SNS_BLE;ALRT_SNS_YLW;APP_ACTIVE;AVERAGE_DATA;BABY_NAME;BASE_STATION_ON;BATT_LEVEL;BIRTHDATE;BLE_MAC_ID;BLE_RSSI;CHARGE_STATUS;CRIT_BATT_ALRT;CRIT_OX_ALRT;DEVICE_PING;DISABLE_LOGGED_DATA;ELEVATION;GENDER;HEART_RATE;HIGH_HR_ALRT;LATITUDE;LIVE_DATA_STREAM;LOCAL_BLE_MAC_ID;LOGGED_DATA_CACHE;LONGITUDE;LOW_BATT_ALRT;LOW_BATT_PRCNT;LOW_HR_ALRT;LOW_INTEG_READ;LOW_OX_ALRT;LOW_PA_ALRT;MOVEMENT;NURSERY_MODE;oem_base_version;oem_sock_version;ON_BOARDING;OTA_ERROR;OTA_STATUS;OXYGEN_LEVEL;PREMATURE;SHARE_DATA;SOCK_CONNECTION;SOCK_DISCON_ALRT;SOCK_DIS_APP_PREF;SOCK_DIS_NEST_PREF;SOCK_OFF;SOCK_REC_PLACED;
1546552539.567462;AC000W00REDACTED;None;None;1;1;1;None;Little Baby;1;81;20190115;EEFE7EREDACTED;0;0;0;0;0;None;None;M;89;0;None;None;E711E4REDACTED;https://ads-field.aylanetworks.com/apiv1/devices/REDACTED/properties/LOGGED_DATA_CACHE/datapoints/REDACTED.json;None;0;None;0;0;0;0;0;0;M2_2_0_0_a078;B2_0_19_0_f331;0;0;0;99;None;None;1;0;None;None;0;0;
```

## Requirements
* Python >= 3.5
* requests
* python-dateutil
* argparse

## Usage
The easiest way to access data from the Owlet is via our command line interface (CLI). 

### Command Line Interface
Here is the build-in help:
```
usage: owlet [-h] [--device DEVICE] [--stream ATTRIBUTES] [--timeout TIMEOUT]
             email password {token,devices,attributes,stream,download}
             [{token,devices,attributes,stream,download} ...]
owlet: error: the following arguments are required: email, password, actions
```

Obtain an authentication token:
```
$ owlet email@email.org password token
Token: 402aba28d94a4493a106a6REDACTED
```

Obtain a listing of all devices in your account:
```
owlet email@email.org password devices
AC000W00REDACTED Online  18.7667 4.1833
```

List all attributes of all devices in your account:
```
$ owlet email@email.org password attributes
AGE_MONTHS_OLD      Age (Months)          None                 None
ALRTS_DISABLED      Disable Alerts        None                 None
ALRT_SNS_BLE        Alert Sense Ble       2018-05-09 20:54:11+00:00 1
ALRT_SNS_YLW        Alert Sense Yellow    2018-05-09 20:54:42+00:00 1
APP_ACTIVE          App Active            2019-01-10 18:50:40+00:00 0
...
```

Contiously poll the service for new data and output in CSV format:
```
$ owlet email@email.org password stream
TIMESTAMP;DSN;AGE_MONTHS_OLD;ALRTS_DISABLED;ALRT_SNS_BLE;ALRT_SNS_YLW;APP_ACTIVE;AVERAGE_DATA;BABY_NAME;BASE_STATION_ON;BATT_LEVEL;BIRTHDATE;BLE_MAC_ID;BLE_RSSI;CHARGE_STATUS;CRIT_BATT_ALRT;CRIT_OX_ALRT;DEVICE_PING;DISABLE_LOGGED_DATA;ELEVATION;GENDER;HEART_RATE;HIGH_HR_ALRT;LATITUDE;LIVE_DATA_STREAM;LOCAL_BLE_MAC_ID;LOGGED_DATA_CACHE;LONGITUDE;LOW_BATT_ALRT;LOW_BATT_PRCNT;LOW_HR_ALRT;LOW_INTEG_READ;LOW_OX_ALRT;LOW_PA_ALRT;MOVEMENT;NURSERY_MODE;oem_base_version;oem_sock_version;ON_BOARDING;OTA_ERROR;OTA_STATUS;OXYGEN_LEVEL;PREMATURE;SHARE_DATA;SOCK_CONNECTION;SOCK_DISCON_ALRT;SOCK_DIS_APP_PREF;SOCK_DIS_NEST_PREF;SOCK_OFF;SOCK_REC_PLACED;
```

Download the `LOGGED_DATA_CACHE` (of currently unknown format):
```
owlet email@email.org password download
��8;������������M=���N@����:���R>����7����9���W:���X<��Z>���\H���_K����@����B����
...
```

### Python
You can take the [CLI implementation](owlet_api/cli.py) as reference. A basic example:
```
# Import Owlet API
from owlet_api.owletapi import OwletAPI

# Instantiate and login
api = OwletAPI('email@email.org', 'password')
api.login()

# Iterate over all devices
for device in api.get_devices():
    # Update the attributes of this device
    device.update()
    
    # Enable data streaming for this device
    device.reactivate()
    
    # Print out all properties
    for name, myproperty in device.get_properties().items():
        print("%-19s %-21s %-20s %s" % (myproperty.name, myproperty.display_name, myproperty.last_update, myproperty.value))
    
```

## What are the properties for a device ?
| Attribute           | Human Readable        | Example value  | Interpretation  | 
| ------------------- | --------------------- | -------------- | ----------
| AGE_MONTHS_OLD      | Age (Months)          | None           | Unknown
| ALRTS_DISABLED      | Disable Alerts        | None           | Unknown
| ALRT_SNS_BLE        | Alert Sense Ble       | 1              | BLE Alert Enabled?
| ALRT_SNS_YLW        | Alert Sense Yellow    | 1              | Yellow Alert Enabled?
| APP_ACTIVE          | App Active            | 0              | Flag set by the App (or this library) to enable data streaming |
| AVERAGE_DATA        | Average Data          | None           | Unknown
| BABY_NAME           | Baby's Name           | Little Baby    | Baby's name as set in the App |
| BASE_STATION_ON     | Base Station On       | 1              | Is base station enabled?
| BATT_LEVEL          | Battery Level (%)     | 95             | Battery Level of the sock
| BIRTHDATE           | Birthdate             | 20190115       | Baby's Birthdate
| BLE_MAC_ID          | Sock BLE Id           | EEFE7EREDACTED | BLE MAC of Sock
| BLE_RSSI            | BLE RSSI              | 0              | Unknown
| CHARGE_STATUS       | Charge Status         | 0              | Is sock charging?
| CRIT_BATT_ALRT      | Crit. Battery Alert   | 0              | Battery Critical Alert
| CRIT_OX_ALRT        | Crit. Oxygen Alert    | 0              | Oxygen Critical Alert
| DEVICE_PING         | Device Ping           | 0              | Unknown
| DISABLE_LOGGED_DATA | Disable Logged Data   | None           | Unknown
| ELEVATION           | Elevation             | None           | Unknown
| GENDER              | Gender                | M              | Baby's Gender
| HEART_RATE          | Heart Rate            | 136            | Baby's Heart Rate
| HIGH_HR_ALRT        | High HR Alert         | 0              | High Heart Rate Alert
| LATITUDE            | Latitude              | None           | Unknown
| LIVE_DATA_STREAM    | Live Data Stream      | None           | Unknown
| LOCAL_BLE_MAC_ID    | Base BLE Mac Id       | E711E4REDACTED | BLE MAC of base station
| LOGGED_DATA_CACHE   | Logged Data Cache     | [https://....json](https://ads-field.aylanetworks.com/apiv1/devices/REDACTED/properties/LOGGED_DATA_CACHE/datapoints/REDACTED.json) | URL of logged data (format unknown)
| LONGITUDE           | Longitude             | None           | Unknown
| LOW_BATT_ALRT       | Low Battery Alert     | 0              | Low Battery Alert
| LOW_BATT_PRCNT      | Low Batt. Percent     | None           | Unknown
| LOW_HR_ALRT         | Low HR Alert          | 0              | Low Heart Rate Alert
| LOW_INTEG_READ      | Low Integrity Read    | 0              | Unknown
| LOW_OX_ALRT         | Low Oxygen Alert      | 0              | Low Oxygen Alert
| LOW_PA_ALRT         | Low Pa Alert          | 0              | Unknown
| MOVEMENT            | Baby Movement         | 1              | Is baby moving?
| NURSERY_MODE        | Nursery Mode          | 0              | Unknown
| oem_base_version    | oem_base_version      | M2_2_0_0_a078  | Unknown
| oem_sock_version    | oem_sock_version      | B2_0_19_0_f331 | Unknown
| ON_BOARDING         | On Boarding           | 0              | Unknown
| OTA_ERROR           | OTA Error             | 0              | Unknown
| OTA_STATUS          | OTA Status            | 0              | Unknown
| OXYGEN_LEVEL        | Oxygen Level          | 96             | Baby's Oxygen Level
| PREMATURE           | Premature             | None           | Unknown
| SHARE_DATA          | Share Data            | None           | Unknown
| SOCK_CONNECTION     | Sock Connection       | 1              | Connection to sock available
| SOCK_DISCON_ALRT    | Sock Disconnect Alert | 0              | Sock disconnected alert
| SOCK_DIS_APP_PREF   | Sock Dis. App Pref.   | None           | Unknown
| SOCK_DIS_NEST_PREF  | Sock Dis. Nest Pref.  | None           | Unknown
| SOCK_OFF            | Sock Off              | 0              | Unknown
| SOCK_REC_PLACED     | Sock Recently Placed  | 0              | Unknown

## Acknowledgements
Several others have implemented APIs for the Owlet Smart Sock. The following inspired me when writing this code:
* https://github.com/angel12/pyowlet
* https://github.com/craigjmidwinter/pyowlet
* https://github.com/mbevand/owlet_monitor

Thank you very much for your work and for open sourcing it!
