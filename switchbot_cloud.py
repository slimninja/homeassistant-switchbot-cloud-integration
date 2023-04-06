# SETUP:
# 1. Move this script to /config/scripts/switchbot_cloud.py
# 2. Add 'switchbot_api_token' and 'switchbot_secret_key' to your secrets.yaml
#    Optional: Define your device id in secrets.yaml, e.g. switchbot_kettle_id and use that to call script
# 3. Add below config to /config/configuration.yaml (sensor and command example)
#
#  Sensor Setup: https://www.home-assistant.io/integrations/sensor.command_line/#usage-of-json-attributes-in-command-output
#  - platform: command_line
#    name: Switchbot Kettle Battery
#    command: 'python3 scripts/switchbot_cloud.py status switchbot_kettle_id'
#    json_attributes:
#      - power
#      - battery
#      - deviceType
#      - deviceMode
#      - version
#      - hubDeviceId
#    scan_interval: 86400
#    value_template: '{{ value_json.battery }}'
#
#  Command Setup: https://www.home-assistant.io/integrations/shell_command/
#  shell_command:
#    switchbot_press_kettle: 'python3 scripts/switchbot_cloud.py press switchbot_kettle_id'
#    switchbot_press_espresso_machine: 'python3 scripts/switchbot_cloud.py press xxxxxxxxxxxx'

import base64
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from http.client import HTTPSConnection
import yaml

SECRETS = None
BASE_URL = 'api.switch-bot.com'

# Helper function for sending requests as HomeAssistant doesnt have the requests module built in
def request(path, data={}, method='GET'):

    # Switchbot authentication using secrets.yaml
    token = SECRETS.get('switchbot_api_token')
    secret =  SECRETS.get('switchbot_secret_key')
    nonce = uuid.uuid4()

    t = int(round(time.time() * 1000))
    string_to_sign = '{}{}{}'.format(token, t, nonce)

    string_to_sign = bytes(string_to_sign, 'utf-8')
    secret = bytes(secret, 'utf-8')

    sign = base64.b64encode(hmac.new(secret, msg=string_to_sign, digestmod=hashlib.sha256).digest())

    encoded_data = json.dumps(data).encode('utf-8')
    headers = {
        "Authorization": str(token),
        "t": str(t),
        "sign": str(sign, 'utf-8'),
        "nonce": str(nonce),
        "Content-Type": "application/json; charset=utf8"
    }

    conn = HTTPSConnection(BASE_URL)
    conn.request(method, path, body=encoded_data, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    response = json.loads(data.decode('utf-8'))

    if response['statusCode'] == 190:
        return response['message']
    elif response['statusCode'] == 100 and response['body']:
        return response['body']
    elif response['statusCode'] == 100:
        return response['message']
    else:
        return response

# Send data to HomeAssistant as pretty printed sysout
def output(data):
    formatted = json.dumps(data, indent=2)
    print(formatted)

# Read from secrets.yaml (check if in current directory, or parent directory)
def get_secrets():
    secrets_filename = 'secrets.yaml'
    current_directory = os.path.dirname(__file__)
    parent_directory = os.path.dirname(current_directory)
    secrets_current_directory = os.path.join(current_directory, secrets_filename)
    secrets_parent_directory = os.path.join(parent_directory, secrets_filename)

    if os.path.exists(secrets_current_directory):
        secrets_path = secrets_current_directory
    elif os.path.exists(secrets_parent_directory):
        secrets_path = secrets_parent_directory
    else:
        raise Exception('missing secrets.yaml')

    with open(secrets_path, 'r') as file:
        global SECRETS
        SECRETS = yaml.safe_load(file)

def main():
    args = sys.argv[1:] # read args from script call
    if len(args) == 1 and args[0] == 'list': # list requires single arg
        args.append(None)
    elif len(args) != 2:
        raise Exception('invalid args')
    command, device_id = args

    get_secrets()

    if command == 'list':
        path = f'/v1.1/devices'
        response = request(path)
        devices = response['deviceList']
        return output(devices)

    # Check if secrets.yaml has the key defined (e.g. switchbot_kettle), else use passed-in id
    device_id = SECRETS.get(device_id, device_id)

    if command == 'status':
        path = f'/v1.1/devices/{device_id}/status'
        response = request(path)
        return output(response)

    if command in ['press', 'turnOn', 'turnOff']:
        path = f'/v1.1/devices/{device_id}/commands'
        data = {"command": command, "commandType": "command"}
        response = request(path, data, 'POST')
        return output(response)

    raise Exception(f'invalid command specified, "{command}"')

if __name__ == "__main__":
    main()
