import json
import os

import requests
from PIL import Image, ImageSequence

GIF_TRANSPARENT_INDEX = 255  # Palette index reserved for transparency, colors use 0-254


def get_package_info(sticker_id: int) -> dict | None:
    """Get sticker package information."""
    url = f"http://dl.stickershop.line.naver.jp/products/0/0/1/{sticker_id}/iphone/productInfo.meta"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Error while fetching sticker information, status code: {response.status_code}")
            print(f"Sticker ID {sticker_id} might not exist or has been removed")
            return None

        return response.json()
    except Exception as error:
        print(f"Error while fetching sticker information: {error}")
        return None


def sanitize_folder_name(folder_name: str) -> str:
    """Sanitize folder name in case of invalid characters appears."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        folder_name = folder_name.replace(char, '_')
    return folder_name.strip()


def save_stickers(sticker_id: int, stickers: list, has_animation: bool, output_path: str):
    """Download stickers and save them to the specified directory.

    :param int sticker_id: Sticker package ID.
    :param list stickers: List of stickers in that series, get from package info.
    :param bool has_animation: Whether the sticker package has animation.
    :param str output_path: Output path to save the stickers
    """
    if has_animation:
        for sticker in stickers:
            single_sticker_id = sticker['id']
            url = (f"http://dl.stickershop.line.naver.jp/products/0/0/1/{sticker_id}/iPhone/"
                   f"animation/{single_sticker_id}@2x.png")
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    with open(f"{output_path}/{single_sticker_id}.apng", 'wb') as f:
                        f.write(response.content)
            except Exception as error:
                print(
                    f"Error while downloading sticker({sticker_id}): {single_sticker_id}: {error}")
            convert_apng_to_gif(f"{output_path}/{single_sticker_id}.apng")

    # Download static stickers even if the package has animation
    for sticker in stickers:
        single_sticker_id = sticker['id']
        url = (f"http://dl.stickershop.line.naver.jp/products/0/0/1/{sticker_id}/iPhone/"
               f"stickers/{single_sticker_id}@2x.png")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(f"{output_path}/{single_sticker_id}.png", 'wb') as f:
                    f.write(response.content)
        except Exception as error:
            print(
                f"Error while downloading sticker({sticker_id}): {single_sticker_id}: {error}")


def convert_apng_to_gif(apng_file_path: str, gif_file_path: str | None = None) -> str | None:
    """Convert APNG to GIF.

    :param str apng_file_path: Path to the APNG file.
    :param str gif_file_path: The generated GIF file path. None to use the same path as APNG file.
    :return str: The path of the generated GIF file, None if failed.
    """
    gif_file_path = gif_file_path or apng_file_path.replace('.apng', '.gif')
    try:
        with Image.open(apng_file_path) as apng:
            frames, durations = [], []
            for frame in ImageSequence.Iterator(apng):
                rgba = frame.convert('RGBA')
                durations.append(frame.info.get('duration', 100))
                # GIF only supports on/off transparency, pixels under 50% alpha become transparent
                transparent_mask = rgba.getchannel('A').point(lambda a: 255 if a < 128 else 0)
                gif_frame = rgba.convert('RGB').quantize(colors=255)
                gif_frame.paste(GIF_TRANSPARENT_INDEX, mask=transparent_mask)
                frames.append(gif_frame)
            frames[0].save(gif_file_path, save_all=True, append_images=frames[1:],
                           duration=durations, loop=apng.info.get('loop', 0), disposal=2,
                           transparency=GIF_TRANSPARENT_INDEX)
    except Exception as error:
        print(f"Error while converting APNG to GIF: {error}")
        return None
    return gif_file_path


def download(sticker_id: int) -> str:
    """Download stickers by sticker package ID.

    :param int sticker_id: Sticker package ID.
    :return str: The path of the downloaded stickers.
    """
    package_info = get_package_info(sticker_id)
    sticker_name = package_info['title']['en']
    folder_path = f"./downloads/stickers/{sticker_id}_{sanitize_folder_name(sticker_name)}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    with open(f"{folder_path}/info.json", "w", encoding="utf-8") as file:
        json.dump(package_info, file, ensure_ascii=False, indent=2)

    sticker_has_animation = package_info.get('hasAnimation', False)
    stickers = package_info['stickers']
    save_stickers(sticker_id, stickers, sticker_has_animation, folder_path)
    return folder_path
