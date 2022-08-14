Shelly
=========

Role used to manage config and firmware update of shelly devices (Allterco Robotics Ltd.)

Requirements
------------

No specific requirements

Role Variables
--------------

Variable name | Description | Example
 --- | --- | ---
username | Username used to connect to shelly api | "admin"
password | Password used to connect to shelly api | "XXXXX"
firmware_list | Firmware list used for checking updates | "https://api.shelly.cloud/files/firmware" (default)
firmware_autoupdate | Define if firmware will be updated during the run | false (default)
settings_apply | Define if settings defined should be applied or only checked | true (default)
wanted_settings | Define the structure (yaml) of config that be applied to shelly device |  see below

### Shelly config
The Shelly config structure could be checked out here : https://shelly-api-docs.shelly.cloud/gen1/#settings
wanted_settings variable should look like that:

```
led_status_disable: false
   discoverable: false
   relays:
     - name: "Channel 1"
     - name: "Channel 2"
   sntp:
     server: time.google.com
   cloud:
     enabled: false
```



Dependencies
------------

No dependencies

Example Playbook
----------------

```
- hosts: all
  gather_facts: no
  roles:
    - shelly

```

License
-------

BSD
