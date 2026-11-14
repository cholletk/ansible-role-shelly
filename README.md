Shelly
======

Role used to manage config and firmware of Shelly devices (Allterco Robotics Ltd.):

- **Gen1** (Shelly 1, 2.5, Dimmer 2, Button1...) through the HTTP `/settings` API;
- **Gen2+** (Plus, Pro, Gen3, Gen4) through the JSON-RPC API (`/rpc`), with the
  device digest authentication (SHA-256) handled by the bundled `shelly_rpc` module.

The generation is detected from `http://<device>/shelly`.

Requirements
------------

- `ansible-core` >= 2.15
- collection `ansible.utils` (Gen1 only): `ansible-galaxy collection install -r requirements.yml`
- the controller must reach the devices over HTTP (tasks run on localhost)

Role Variables
--------------

Variable name | Description | Default
 --- | --- | ---
username | Username used to connect to the shelly API (always `admin` on Gen2+) | `"admin"`
password | Device password (put it in a vault). Gen2+: also enables authentication if it is off | undefined
firmware_autoupdate | Update the firmware during the run | `false`
settings_apply | Apply the settings (`false`: only check them) | `true`
firmware_list | Gen1: firmware list used for checking updates | `"https://api.shelly.cloud/files/firmware"`
password_unconditionnal_apply | Gen1: always resend the login block | `true`
wanted_settings | Gen1: structure of the `/settings` config to apply | see below
shelly_gen2_config | Gen2+: wanted config per component (`sys`, `mqtt`, `switch:0`, `input:1`...) | `{}`
shelly_gen2_secret_keys | Gen2+: write-only keys never returned by `GetConfig` | `["pass"]`
shelly_gen2_force_secrets | Gen2+: send components holding a secret on every run | `false`
shelly_reboot_when_required | Gen2+: reboot when a `SetConfig` answers `restart_required` | `true`
shelly_scripts | Gen2+: embedded scripts to deploy (`name`, `src` template, `enable`, `start`) | `[]`
shelly_gen2_firmware_stage | Gen2+: firmware channel used by `Shelly.Update` | `"stable"`

### Gen1 config
The structure is documented here: https://shelly-api-docs.shelly.cloud/gen1/#settings

```yaml
wanted_settings:
  led_status_disable: false
  discoverable: false
  relays:
    - name: "Channel 1"
    - name: "Channel 2"
  sntp:
    server: time.google.com
  cloud:
    enabled: false
  login:                       # always sent as one request
    enabled: true
    username: admin
    password: "{{ vault_shelly_password }}"
```

### Gen2+ config
Component names and keys are the ones of `Shelly.GetConfig`
(https://shelly-api-docs.shelly.cloud/gen2/). Only the listed keys are managed and
a component is written only when one of them differs.

```yaml
password: "{{ vault_shelly_password }}"
shelly_gen2_config:
  sys:
    device: {name: "Interrupteur chambre"}
  switch:0:
    name: "Alim lampe"
    in_mode: detached
    initial_state: "on"
  mqtt:
    enable: true
    server: "192.168.128.52:1883"
    user: shelly_mqtt
    pass: "{{ vault_shelly_mqtt_password }}"
shelly_scripts:
  - name: chambre_lampe
    src: "{{ playbook_dir }}/scripts/chambre_lampe.js"
```

Scripts are Jinja2 templates and must be plain ASCII: the device does not keep
multi-byte characters, which would make the script re-upload on every run.

Dependencies
------------

No dependencies

Example Playbook
----------------

```yaml
- hosts: shelly
  gather_facts: false
  roles:
    - shelly
```

```yaml
# inventory
shelly:
  hosts:
    interrupteur-chambre:
      ansible_host: 192.168.1.62
  vars:
    ansible_connection: local
```

```sh
ansible-playbook -i inventory.yml site.yml -e @secrets.vault.yml --ask-vault-pass --check
```

License
-------

GNU General Public License v3.0 or later.

See [COPYING](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
