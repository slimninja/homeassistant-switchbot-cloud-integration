# SETUP:
# 1. Move this script to /config/scripts/switchbot_control.py
# 2. Run 'pip install --target=/config/scripts/ python-switchbot' to install package in the same directory as script
# 3. Add 'switchbot_api_token' and 'switchbot_secret_key' to your secrets.yaml
#    Optional: Define your device id in secrets.yaml, e.g. switchbot_kettle_id and use that to call script
# 4. Add below config to /config/configuration.yaml (sensor and command example)
#
#  Sensor Setup: https://www.home-assistant.io/integrations/sensor.command_line/#usage-of-json-attributes-in-command-output
#  - platform: command_line
#    name: Switchbot Kettle Battery
#    command: 'python3 scripts/switchbot_control.py status switchbot_kettle_id'
#    json_attributes:
#      - battery
#      - version
#    scan_interval: 86400
#    value_template: '{{ value_json.battery }}'
#
#  Command Setup: https://www.home-assistant.io/integrations/shell_command/
#  shell_command:
#    switchbot_press_kettle: 'python3 scripts/switchbot_control.py press switchbot_kettle_id'
#    switchbot_press_espresso_machine: 'python3 scripts/switchbot_control.py press xxxxxxxxxxxx'

import json
import sys
import uuid
import yaml
from switchbot import SwitchBot

# Check arguments
args = sys.argv[1:]
if len(args) == 0 or len(args) > 2:
    raise Exception('invalid args')

# Switchbot API authentication
# Read from secrets.yaml (assuming file is in parent folder)
# Else remove below lines and hardcode token/secret
with open('/config/secrets.yaml', 'r') as file:
    try:
        secrets = yaml.safe_load(file)
    except yaml.YAMLError as e:
        print(e)

token = secrets.get('switchbot_api_token')
secret =  secrets.get('switchbot_secret_key')
switchbot = SwitchBot(token=token, secret=secret, nonce=str(uuid.uuid4()))

# Parse arguments from sys args
command = args[0]
id = args[1] if len(args) == 2 else None
id = secrets.get(id, id) # check if secrets.yaml has the key defined (e.g. switchbot_kettle_id), else use passed-in id

if command == 'list':
    devices = switchbot.devices()
    for device in devices:
        print(vars(device))
elif command == 'status':
    device = switchbot.device(id=id)
    data = device.status()
    print(json.dumps(data))
elif command in ['boop' 'toggle', 'press']:
    device = switchbot.device(id=id)
    device.command('press')
else:
    raise Exception('invalid command')

