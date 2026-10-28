import asyncio

import uvicorn

import download_manager
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
    client.tree.command(name="about", description="關於此機器人, 查看目前連動備份的服務")(about)
    client.tree.command(name="help", description="此指令會協助你使用此機器人")(help)
    client.tree.command(name="link", description="此指令用來與Line群組綁定，並進行連動備份")(link)
    client.tree.command(name="unlink",
                        description="此指令用來解除與Line群組的綁定, 並取消連動備份")(unlink)

    await client.start(config.get('discord_bot_token'))


async def main():
    # Initialize the cache
    sync_channels_cache.load_all_sync_channels()

    # Trim the downloads folder in case it grew over the limit while the bot was offline
    if config['downloads_mode'] == download_manager.MODE_SIZE_LIMIT:
        download_manager.enforce_size_limit(config['downloads_max_size_mb'])

    await asyncio.gather(
        run_linebot(),
        run_discord_bot()
    )


if __name__ == '__main__':
    asyncio.run(main())
