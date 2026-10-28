import json
import random
import sys
import time
from os.path import exists

import yaml
from yaml import SafeLoader

import download_manager
from cache import sync_channels_cache


def graceful_exit(message=""):
    """Exit program gracefully with a pause for user to read the message."""
    if message:
        print(message)
    input("Press Enter to exit...")
    sys.exit()


def config_file_generator():
    """Generate the template of config file"""
    with open('config.yml', 'w', encoding="utf8") as file:
        file.write("""# ++--------------------------------++
# | LineBackupToDiscord (MIT LICENSE)|
# | Made by LD               v0.1.0  |
# ++--------------------------------++


# Line Channel Access Token & Secret
# You can get it from https://developers.line.biz/console/
line_channel_access_token: ''
line_channel_secret: ''

# Discord Bot token
# You can get it from https://discord.com/developers/applications
discord_bot_token: ''

# Backend server configuration, aka the webhook server port for LINE.
# If you change port, make sure to change the port in your reverse proxy(ngrok etc..) as well.
webhook_port: 5000

# Downloads folder settings.
# Pictures, videos, audios, files and stickers are saved in the downloads folder, pick how to manage it:
#   'unlimited'    - Keep every file forever (default)
#   'size_limit'   - Keep the folder under downloads_max_size_mb, the least recently used files
#                    are removed automatically when it gets bigger than that
#   'instant_burn' - Remove pictures, videos, audios and files right after they are sent to Discord.
#                    Stickers are kept as a cache, limited by downloads_max_size_mb
downloads_mode: 'unlimited'
# Max size of the downloads folder in MB, used when downloads_mode is 'size_limit' or 'instant_burn'
downloads_max_size_mb: 1024


# (Optional settings)
# You can fill in your own bot invite link and hosted by information
# This will be shown when someone types /about
# Noted that if you share your bot invite link, anyone can invite your bot to their server
bot_hosted_by: 'PlayfunI Network'
line_bot_invite_link: ''
discord_bot_invite_link: ''
"""
                   )
        file.close()
    graceful_exit("Config file created successfully.\n"
                  "Please fill in config.yml then restart the program!")


def read_config():
    """Read config file.

    Check if config file exists, if not, create one.
    if exists, read config file and return config with dict type.

    :rtype: dict
    """
    if not exists('./config.yml'):
        with open('config.yml', 'w', encoding="utf8"):
            config_file_generator()

    try:
        with open('config.yml', encoding="utf8") as file:
            data = yaml.load(file, Loader=SafeLoader)
            config = {
                'line_channel_access_token': data['line_channel_access_token'],
                'line_channel_secret': data['line_channel_secret'],
                'discord_bot_token': data['discord_bot_token'],
                'webhook_port': data['webhook_port'],
                'downloads_mode': data.get('downloads_mode', download_manager.MODE_UNLIMITED),
                'downloads_max_size_mb': data.get('downloads_max_size_mb', 1024),
                'bot_hosted_by': data.get('bot_hosted_by', 'PlayfunI Network'),
                'line_bot_invite_link': data['line_bot_invite_link'],
                'discord_bot_invite_link': data['discord_bot_invite_link']
            }
            file.close()
    except (KeyError, TypeError):
        graceful_exit(
            "An error occurred while reading config.yml, please check if the file is corrected filled.\n"
            "If the problem can't be solved, consider delete config.yml and restart the program.\n")

    required_fields = ['line_channel_access_token', 'line_channel_secret',
                       'discord_bot_token', 'webhook_port']
    for field in required_fields:
        if field not in config or not config[field]:
            graceful_exit(f"Missing required field: {field} in config.yml")
            sys.exit()

    if config['downloads_mode'] not in download_manager.MODES:
        graceful_exit(f"Invalid downloads_mode: {config['downloads_mode']} in config.yml, "
                      f"must be one of {', '.join(download_manager.MODES)}")
    max_size = config['downloads_max_size_mb']
    if isinstance(max_size, bool) or not isinstance(max_size, (int, float)) or max_size <= 0:
        graceful_exit(f"Invalid downloads_max_size_mb: {max_size} in config.yml, "
                      f"must be a number bigger than 0")
    return config


def read_sync_channels():
    """Read sync_channels.json file."""
    if not exists('./sync_channels.json'):
        print("sync_channels.json not found, create one by default.")
        with open('sync_channels.json', 'w', encoding="utf8") as file:
            json.dump([], file, indent=4)
            file.close()
    data = json.load(open('sync_channels.json', 'r', encoding="utf8"))
    return data


def add_new_sync_channel(line_group_id: str, line_group_name: str, discord_channel_id: int,
                         discord_channel_name: str, discord_channel_webhook: str):
    """Add new sync channel.

    :param str line_group_id: Line group id.
    :param str line_group_name: Line group name.
    :param int discord_channel_id: Discord channel id.
    :param str discord_channel_name: Discord channel name.
    :param str discord_channel_webhook: Discord channel webhook.
    """
    data = json.load(open('sync_channels.json', 'r', encoding="utf8"))
    if not data:  # If the file is empty
        sub_num = 1
    else:  # Get the max sub_num and add 1
        max_dict = max(data, key=lambda x: x.get('sub_num', 0))
        sub_num = max_dict.get('sub_num', 0) + 1
    folder_name = f'{line_group_name}_{discord_channel_name}'
    data.append({
        'sub_num': sub_num,
        'folder_name': folder_name,
        'line_group_id': line_group_id,
        'line_group_name': line_group_name,
        'discord_channel_id': discord_channel_id,
        'discord_channel_name': discord_channel_name,
        'discord_channel_webhook': discord_channel_webhook
    })
    update_json('sync_channels.json', data)
    sync_channels_cache.add_sync_channel(sub_num, folder_name, line_group_id, line_group_name,
                                         discord_channel_id, discord_channel_name,
                                         discord_channel_webhook)


def remove_sync_channel(line_group_id: str = None, discord_channel_id: int = None):
    """Remove sync channel.

    :param str line_group_id: Line group id.
    :param int discord_channel_id: Discord channel id.
    """
    data = json.load(open('sync_channels.json', 'r', encoding="utf8"))
    if line_group_id:
        data = [x for x in data if x['line_group_id'] != line_group_id]
    elif discord_channel_id:
        data = [x for x in data if x['discord_channel_id'] != discord_channel_id]
    update_json('sync_channels.json', data)
    sync_channels_cache.remove_sync_channel(line_group_id, discord_channel_id)


def generate_binding_code(line_group_id: str, line_group_name: str) -> int:
    """Generate binding code.

    :param str line_group_id: Line group id.
    :param str line_group_name: Line group name.
    :return int: Binding code.
    """
    if not exists('./binding_codes.json'):
        with open('binding_codes.json', 'w', encoding="utf8") as file:
            json.dump({}, file, indent=4)
            file.close()
    data = json.load(open('binding_codes.json', 'r', encoding="utf8"))
    binding_code = random.randint(100000, 999999)
    data[binding_code] = {'line_group_id': line_group_id, 'line_group_name': line_group_name,
                          'expiration': time.time() + 300}
    update_json('binding_codes.json', data)
    return binding_code


def remove_binding_code(binding_code: int):
    """Remove binding code from binding_codes.json.

    :param int binding_code: Binding code.
    """
    data = json.load(open('binding_codes.json', 'r', encoding="utf8"))
    # JSON object keys are always strings
    if str(binding_code) in data:
        data.pop(str(binding_code))
        update_json('binding_codes.json', data)


def get_binding_code_info(binding_code: int) -> dict | None:
    """Get binding code info.

    :param int binding_code: Binding code.
    :return dict: Return dict contains line_group_id and expiration if it exists, else None
    """
    if not exists('./binding_codes.json'):
        return None
    data = json.load(open('binding_codes.json', 'r', encoding="utf8"))
    return data.get(str(binding_code))


def update_json(file_name: str, data: dict):
    """Update a json file.

    :param str file_name: The file to update.
    :param dict data: The data to update.
    """
    with open(file_name, 'w', encoding="utf8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
        file.close()
