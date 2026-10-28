import asyncio

import uvicorn

import download_manager
import messages
import utilities as utils
from cache import sync_channels_cache
from discord_bot import client, on_ready, about, help, link, unlink
from line_bot import app as fastapi_app

config = utils.read_config()


async def run_linebot():
    host_config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=config['webhook_port'])
    server = uvicorn.Server(host_config)
    await server.serve()


async def run_discord_bot():
    client.event(on_ready)

    # Register commands
    for name, command in (("about", about), ("help", help), ("link", link), ("unlink", unlink)):
        client.tree.command(name=name, description=messages.COMMAND_DESCRIPTIONS[name])(command)

    await client.start(config.get('discord_bot_token'))


async def main():
    # Initialize the cache
    sync_channels_cache.load_all_sync_channels()

    # Trim the downloads folder in case it grew over the limit while the bot was offline
    if config['downloads_mode'] in (download_manager.MODE_SIZE_LIMIT,
                                    download_manager.MODE_INSTANT_BURN):
        download_manager.enforce_size_limit(config['downloads_max_size_mb'])

    await asyncio.gather(
        run_linebot(),
        run_discord_bot()
    )


if __name__ == '__main__':
    asyncio.run(main())
