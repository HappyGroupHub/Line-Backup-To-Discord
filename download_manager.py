import os
import shutil

DOWNLOADS_DIR = './downloads'
STICKERS_DIR = os.path.join(DOWNLOADS_DIR, 'stickers')

# Modes for the downloads folder, set by `downloads_mode` in config.yml
MODE_UNLIMITED = 'unlimited'
MODE_SIZE_LIMIT = 'size_limit'
MODE_INSTANT_BURN = 'instant_burn'
MODES = (MODE_UNLIMITED, MODE_SIZE_LIMIT, MODE_INSTANT_BURN)


def get_size(path: str) -> int:
    """Get the size of a file, or the total size of every file inside a folder.

    :param str path: Path to a file or a folder.
    :return int: Size in bytes.
    """
    if os.path.isfile(path):
        return os.path.getsize(path)
    total = 0
    for root, _, files in os.walk(path):
        for file_name in files:
            try:
                total += os.path.getsize(os.path.join(root, file_name))
            except OSError:  # File removed while walking
                continue
    return total


def list_removable_items() -> list:
    """List everything in the downloads folder that can be removed to free up space.

    A sticker package folder counts as one item, so a package is never left half deleted.
    Every other file counts as one item on its own.

    :return list: List of (last_used_time, size, path), oldest first.
    """
    items = []
    if not os.path.exists(DOWNLOADS_DIR):
        return items
    sticker_dir = os.path.abspath(STICKERS_DIR)
    for root, dirs, files in os.walk(DOWNLOADS_DIR):
        if os.path.abspath(root) == sticker_dir:
            for package in dirs:
                package_path = os.path.join(root, package)
                items.append((os.path.getmtime(package_path), get_size(package_path),
                              package_path))
            dirs.clear()  # Packages are handled as a whole, don't walk into them
            for file_name in files:  # Loose files in the stickers folder, if any
                file_path = os.path.join(root, file_name)
                items.append((os.path.getmtime(file_path), os.path.getsize(file_path),
                              file_path))
            continue
        for file_name in files:
            file_path = os.path.join(root, file_name)
            items.append((os.path.getmtime(file_path), os.path.getsize(file_path), file_path))
    items.sort(key=lambda item: item[0])
    return items


def remove(path: str):
    """Remove a file or a folder, ignore it if it's already gone.

    :param str path: Path to a file or a folder.
    """
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except FileNotFoundError:
        pass
    except OSError as error:
        print(f"Failed to remove {path}: {error}")


def enforce_size_limit(max_size_mb: float) -> int:
    """Remove the least recently used files until the downloads folder fits in the size limit.

    :param float max_size_mb: Max size of the downloads folder in MB.
    :return int: Number of bytes freed.
    """
    max_size = int(max_size_mb * 1024 * 1024)
    items = list_removable_items()
    total = sum(size for _, size, _ in items)
    freed = 0
    for _, size, path in items:
        if total - freed <= max_size:
            break
        remove(path)
        freed += size
    if freed:
        print(f"Downloads folder exceeded {max_size_mb} MB, "
              f"removed {freed / 1024 / 1024:.2f} MB of old files.")
    return freed


def mark_as_used(path: str):
    """Update the last used time of a file or folder, so it won't be removed first.

    :param str path: Path to a file or a folder.
    """
    try:
        os.utime(path)
    except OSError:
        pass


def handle_sent_file(file_path: str, config: dict):
    """Clean up the downloads folder after a file has been sent to Discord.

    :param str file_path: Path of the file that has just been sent.
    :param dict config: Config read from config.yml.
    """
    mode = config['downloads_mode']
    if mode == MODE_INSTANT_BURN:
        sticker_dir = os.path.abspath(STICKERS_DIR)
        parent_dir = os.path.dirname(os.path.abspath(file_path))
        if os.path.dirname(parent_dir) == sticker_dir:  # Remove the whole sticker package
            remove(parent_dir)
        else:
            remove(file_path)
    elif mode == MODE_SIZE_LIMIT:
        enforce_size_limit(config['downloads_max_size_mb'])
