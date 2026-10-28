import os

import requests

from line_sticker_downloader import convert_apng_to_gif

EMOJIS_DIR = './downloads/emojis'
# LINE doesn't document where emoji images are, this is the CDN the LINE store uses.
# The iPhone version is tried first, and the android version if it's not there.
EMOJI_BASE_URL = "https://stickershop.line-scdn.net/sticonshop/v1/sticon/{product_id}/{device}"
EMOJI_DEVICES = ('iPhone', 'android')


def get_emoji_spans(text: str, emojis: list) -> list | None:
    """Find where each LINE emoji is in the text.

    LINE counts the emoji index in UTF-16 code units, which only differs from Python's string
    index when the text has characters outside the BMP (e.g. Unicode emoji). Both ways are tried,
    and a span is only trusted if it looks like a LINE emoji placeholder such as "(hello)".

    :param str text: Text of the message.
    :param list emojis: Emoji objects from the LINE webhook, each has index and length.
    :return list: List of (start, end) Python string indexes, None if they can't be found.
    """
    # Map UTF-16 offsets to Python string indexes
    utf16_to_index = {}
    offset = 0
    for i, char in enumerate(text):
        utf16_to_index[offset] = i
        offset += 2 if ord(char) > 0xFFFF else 1
    utf16_to_index[offset] = len(text)

    def is_placeholder(start, end):
        return start is not None and end is not None and start < end \
            and text[start] == '(' and text[end - 1] == ')'

    spans = []
    for emoji in emojis:
        start = utf16_to_index.get(emoji.index)
        end = utf16_to_index.get(emoji.index + emoji.length)
        if not is_placeholder(start, end):
            start, end = emoji.index, emoji.index + emoji.length
            if end > len(text) or not is_placeholder(start, end):
                return None
        spans.append((start, end))
    return spans


def is_emoji_only(text: str, emojis: list) -> bool:
    """Check if a text message only contains LINE emojis.

    :param str text: Text of the message.
    :param list emojis: Emoji objects from the LINE webhook.
    :return bool: True if there's nothing but LINE emojis and spaces in the text.
    """
    spans = get_emoji_spans(text, emojis)
    if not spans:
        return False
    remaining = text
    for start, end in sorted(spans, reverse=True):
        remaining = remaining[:start] + remaining[end:]
    return remaining.strip() == ''


def download(product_id: str, emoji_id: str) -> str | None:
    """Download a LINE emoji, animated ones are converted to GIF.

    Emojis are cached in downloads/emojis/<product_id>/, so each one is only downloaded once.

    :param str product_id: Product ID of the LINE emoji set.
    :param str emoji_id: ID of the emoji inside the set.
    :return str: Path of the emoji file, None if failed.
    """
    folder_path = f"{EMOJIS_DIR}/{product_id}"
    for ext in ('gif', 'png'):
        file_path = f"{folder_path}/{emoji_id}.{ext}"
        if os.path.exists(file_path):
            return file_path
    os.makedirs(folder_path, exist_ok=True)

    errors = []
    for device in EMOJI_DEVICES:
        base_url = EMOJI_BASE_URL.format(product_id=product_id, device=device)
        try:
            file_path, status_code = download_from(base_url, folder_path, emoji_id)
        except Exception as error:
            errors.append(f"{device}: {error}")
            continue
        if file_path:
            return file_path
        errors.append(f"{device}: status code {status_code}")

    print(f"Error while downloading emoji({product_id}): {emoji_id}, {', '.join(errors)}")
    # Don't leave an empty folder behind for an emoji set that couldn't be downloaded
    if not os.listdir(folder_path):
        os.rmdir(folder_path)
    return None


def download_from(base_url: str, folder_path: str, emoji_id: str) -> tuple[str | None, int]:
    """Download a LINE emoji from one CDN path, animated ones are converted to GIF.

    :param str base_url: CDN URL of the emoji set, without the file name.
    :param str folder_path: Folder to save the emoji in.
    :param str emoji_id: ID of the emoji inside the set.
    :return tuple[str | None, int]: Path of the emoji file (None if failed) and the status code.
    """
    # Animated emojis are APNG files, static emojis don't have the animation version
    response = requests.get(f"{base_url}/{emoji_id}_animation.png", timeout=10)
    if response.status_code == 200:
        apng_path = f"{folder_path}/{emoji_id}.apng"
        with open(apng_path, 'wb') as file:
            file.write(response.content)
        gif_path = convert_apng_to_gif(apng_path)
        os.remove(apng_path)
        if gif_path:
            return gif_path, response.status_code

    response = requests.get(f"{base_url}/{emoji_id}.png", timeout=10)
    if response.status_code != 200:
        return None, response.status_code
    file_path = f"{folder_path}/{emoji_id}.png"
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path, response.status_code
