#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: shelly_rpc
short_description: Call a Shelly Gen2+ JSON-RPC method
description:
  - Sends one JSON-RPC call to a Shelly Gen2/Gen3/Gen4 device (C(POST /rpc)).
  - Handles the device digest authentication (SHA-256), which the C(uri)
    module cannot do.
  - Read methods (C(*.Get*), C(*.List), C(Shelly.CheckForUpdate)) never report a change.
options:
  host:
    description: Device IP or hostname.
    required: true
    type: str
  method:
    description: RPC method, e.g. C(Switch.GetConfig).
    required: true
    type: str
  params:
    description: RPC parameters.
    type: dict
    default: {}
  username:
    description: Always C(admin) on Shelly Gen2.
    type: str
    default: admin
  password:
    description: Device password. Leave empty when authentication is disabled.
    type: str
    no_log: true
  timeout:
    type: int
    default: 10
"""

RETURN = r"""
result:
  description: The C(result) member of the RPC response.
  returned: success
  type: raw
"""

import hashlib
import json
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError

READ_ONLY_SUFFIXES = (".GetConfig", ".GetStatus", ".GetDeviceInfo", ".GetCode", ".List",
                      ".ListMethods", ".CheckForUpdate", ".GetComponents")


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _post(url, payload, timeout):
    """Return (http_status, decoded_json, www_authenticate) without raising on 401."""
    try:
        resp = open_url(url, method="POST", data=json.dumps(payload),
                        headers={"Content-Type": "application/json"}, timeout=timeout)
        return resp.getcode(), json.loads(resp.read()), None
    except HTTPError as err:
        body = err.read()
        try:
            decoded = json.loads(body)
        except ValueError:
            decoded = {"error": {"code": err.code, "message": body.decode("utf-8", "replace")}}
        return err.code, decoded, err.headers.get("WWW-Authenticate")


def _parse_challenge(header):
    # Digest qop="auth", realm="shellyplus2pm-xxxx", nonce="1794667948", algorithm=SHA-256
    fields = {}
    for part in header.split(" ", 1)[1].split(","):
        key, _, value = part.strip().partition("=")
        fields[key] = value.strip('"')
    return fields


def call(host, method, params, username, password, timeout):
    url = "http://%s/rpc" % host
    payload = {"id": 1, "method": method, "params": params or {}}
    status, body, www_auth = _post(url, payload, timeout)
    if status == 401:
        if not password:
            raise RuntimeError("device requires authentication but no password was given")
        challenge = _parse_challenge(www_auth)
        realm, nonce = challenge["realm"], challenge["nonce"]
        cnonce = os.urandom(8).hex()
        ha1 = _sha256("%s:%s:%s" % (username, realm, password))
        ha2 = _sha256("dummy_method:dummy_uri")
        response = _sha256("%s:%s:1:%s:auth:%s" % (ha1, nonce, cnonce, ha2))
        # JSON-RPC "auth" object (Shelly Gen2 docs): nonce must be sent as a number.
        payload["auth"] = {"realm": realm, "username": username, "nonce": int(nonce),
                           "cnonce": cnonce, "response": response, "algorithm": "SHA-256"}
        status, body, _ = _post(url, payload, timeout)
    if "error" in body:
        raise RuntimeError("RPC %s failed: %s" % (method, body["error"]))
    return body.get("result")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            method=dict(type="str", required=True),
            params=dict(type="dict", default={}),
            username=dict(type="str", default="admin"),
            password=dict(type="str", no_log=True),
            timeout=dict(type="int", default=10),
        ),
        supports_check_mode=True,
    )
    method = module.params["method"]
    read_only = method.endswith(READ_ONLY_SUFFIXES) or method == "Shelly.GetDeviceInfo"
    if module.check_mode and not read_only:
        module.exit_json(changed=True, result=None)
    try:
        result = call(module.params["host"], method, module.params["params"],
                      module.params["username"], module.params["password"], module.params["timeout"])
    except Exception as err:  # noqa: BLE001 - surface any device/network error to the play
        module.fail_json(msg=str(err))
    module.exit_json(changed=not read_only, result=result)


if __name__ == "__main__":
    main()
