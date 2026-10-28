import asyncio
import time

import discord
from discord import app_commands
from discord.ext import commands

import line_bot
import messages
import utilities as utils
from cache import sync_channels_cache

config = utils.read_config()

client = commands.Bot(command_prefix="!", intents=discord.Intents.default())

EMBED_COLOR = 0x2ecc71
UNLINK_EMBED_COLOR = 0x95a5a6


async def on_ready():
    """Initialize discord bot."""
    print("Bot is ready.")
    try:
        synced = await client.tree.sync()
        print(f"Synced {synced} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


def push_line_message(line_group_id: str, message: str):
    """Push a message to LINE, without failing the Discord command if LINE can't be reached.

    :param str line_group_id: LINE group ID.
    :param str message: Message to push.
    """
    try:
        line_bot.push_message(line_group_id, message)
    except Exception as error:
        print(f"Failed to push message to LINE group {line_group_id}: {error}")


@app_commands.describe()
async def about(interaction: discord.Interaction):
    subscribed_info = sync_channels_cache.get_info_by_dc_channel_id(interaction.channel.id)
    all_commands = await client.tree.fetch_commands()
    help_command = discord.utils.get(all_commands, name="help")
    embed_message = discord.Embed(title=messages.BOT_TITLE,
                                  description=messages.about_description(help_command.mention),
                                  color=EMBED_COLOR)
    embed_message.set_author(name=client.user.name, icon_url=client.user.avatar)
    if subscribed_info:
        status = messages.about_bound(subscribed_info['line_group_name'])
    else:
        status = messages.ABOUT_NOT_BOUND
    embed_message.add_field(name=messages.ABOUT_STATUS_FIELD, value=status, inline=False)
    embed_message.add_field(name="作者", value="LD", inline=True)
    embed_message.add_field(name="架設者", value=config['bot_hosted_by'], inline=True)
    embed_message.add_field(name="版本", value=utils.VERSION, inline=True)
    await interaction.response.send_message(embed=embed_message, view=AboutCommandView())


class AboutCommandView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=0)
        github_row = 0
        # Link buttons need a URL, so skip the invite links that aren't filled in config.yml
        if config.get('line_bot_invite_link'):
            self.add_item(discord.ui.Button(label="Line Bot邀請連結",
                                            url=config['line_bot_invite_link'],
                                            style=discord.ButtonStyle.link,
                                            emoji="💬"))
            github_row = 1
        if config.get('discord_bot_invite_link'):
            self.add_item(discord.ui.Button(label="Discord Bot邀請連結",
                                            url=config['discord_bot_invite_link'],
                                            style=discord.ButtonStyle.link,
                                            emoji="🤖"))
            github_row = 1
        self.add_item(discord.ui.Button(label="Github原始碼",
                                        url="https://github.com/HappyGroupHub/Line-Backup-To-Discord",
                                        style=discord.ButtonStyle.link,
                                        emoji="🔬", row=github_row))
        self.add_item(discord.ui.Button(label="使用條款與隱私政策",
                                        url="https://github.com/HappyGroupHub/Line-Backup-To-Discord",
                                        style=discord.ButtonStyle.link,
                                        emoji="💡", row=github_row))


@app_commands.describe()
async def help(interaction: discord.Interaction):
    all_commands = await client.tree.fetch_commands()
    about_command = discord.utils.get(all_commands, name="about")
    link_command = discord.utils.get(all_commands, name="link")
    unlink_command = discord.utils.get(all_commands, name="unlink")
    embed_message = discord.Embed(title=f"{messages.BOT_TITLE}｜使用說明",
                                  description=messages.help_description(
                                      about_command.mention, link_command.mention,
                                      unlink_command.mention),
                                  color=EMBED_COLOR)
    embed_message.set_author(name=client.user.name, icon_url=client.user.avatar)
    await interaction.response.send_message(embed=embed_message)


@app_commands.describe(binding_code=messages.LINK_CODE_DESCRIPTION)
async def link(interaction: discord.Interaction, binding_code: int):
    # Threads and DMs can't have webhooks
    if not hasattr(interaction.channel, 'create_webhook'):
        await interaction.response.send_message(messages.LINK_WRONG_CHANNEL, ephemeral=True)
        return
    subscribed_info = sync_channels_cache.get_info_by_dc_channel_id(interaction.channel.id)
    if subscribed_info:
        await interaction.response.send_message(
            messages.link_channel_already_bound(subscribed_info['line_group_name']),
            ephemeral=True)
        return

    binding_info = utils.get_binding_code_info(binding_code)
    if binding_info is None:
        await interaction.response.send_message(messages.LINK_INVALID_CODE, ephemeral=True)
        return
    if binding_info['expiration'] < time.time():
        utils.remove_binding_code(binding_code)
        await interaction.response.send_message(messages.LINK_EXPIRED_CODE, ephemeral=True)
        return

    try:
        webhook = await interaction.channel.create_webhook(name="Line訊息同步")
    except discord.Forbidden:
        await interaction.response.send_message(messages.LINK_MISSING_PERMISSION, ephemeral=True)
        return
    utils.add_new_sync_channel(binding_info['line_group_id'], binding_info['line_group_name'],
                               interaction.channel.id, interaction.channel.name, webhook.url)
    utils.remove_binding_code(binding_code)

    embed_message = discord.Embed(title=messages.LINK_SUCCESS_TITLE,
                                  description=messages.LINK_SUCCESS_DESCRIPTION,
                                  color=EMBED_COLOR)
    embed_message.add_field(name=messages.FIELD_LINE_GROUP,
                            value=binding_info['line_group_name'], inline=True)
    embed_message.add_field(name=messages.FIELD_DISCORD_CHANNEL,
                            value=interaction.channel.mention, inline=True)
    embed_message.set_footer(text=messages.LINK_SUCCESS_FOOTER)
    await interaction.response.send_message(embed=embed_message)
    push_line_message(binding_info['line_group_id'],
                      messages.line_link_success(binding_info['line_group_name'],
                                                 interaction.channel.name))


@app_commands.describe()
async def unlink(interaction: discord.Interaction):
    subscribed_info = sync_channels_cache.get_info_by_dc_channel_id(interaction.channel.id)
    if not subscribed_info:
        await interaction.response.send_message(messages.UNLINK_NOT_BOUND, ephemeral=True)
        return
    view = UnlinkConfirmation(subscribed_info, interaction)
    await interaction.response.send_message(
        messages.unlink_confirm(subscribed_info['line_group_name']), view=view, ephemeral=True)


class UnlinkConfirmation(discord.ui.View):
    def __init__(self, subscribed_info: dict, original_interaction: discord.Interaction):
        super().__init__(timeout=60)
        self.subscribed_info = subscribed_info
        self.original_interaction = original_interaction

    async def on_timeout(self):
        try:
            await self.original_interaction.edit_original_response(
                content=messages.UNLINK_TIMED_OUT, view=None)
        except discord.HTTPException:
            pass  # The message may be dismissed already

    @discord.ui.button(label=messages.UNLINK_CONFIRM_LABEL, style=discord.ButtonStyle.danger)
    async def unlink_confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        info = self.subscribed_info
        # Someone else might have unlinked it while this confirmation was open
        if not sync_channels_cache.get_info_by_dc_channel_id(info['discord_channel_id']):
            await interaction.response.edit_message(content=messages.UNLINK_NOT_BOUND, view=None)
            return
        utils.remove_sync_channel(discord_channel_id=info['discord_channel_id'])
        try:
            webhook = discord.SyncWebhook.from_url(info['discord_channel_webhook'])
            await asyncio.to_thread(webhook.delete)
        except (discord.HTTPException, ValueError):
            pass  # The webhook may be deleted manually already

        await interaction.response.edit_message(content=messages.UNLINK_DONE, view=None)
        embed_message = discord.Embed(title=messages.UNLINK_SUCCESS_TITLE,
                                      description=messages.UNLINK_SUCCESS_DESCRIPTION,
                                      color=UNLINK_EMBED_COLOR)
        embed_message.add_field(name=messages.FIELD_LINE_GROUP,
                                value=info['line_group_name'], inline=True)
        embed_message.add_field(name=messages.FIELD_DISCORD_CHANNEL,
                                value=f"<#{info['discord_channel_id']}>", inline=True)
        embed_message.set_footer(text=messages.unlink_success_footer(interaction.user.display_name))
        await interaction.followup.send(embed=embed_message)
        push_line_message(info['line_group_id'],
                          messages.line_unlink_success(info['line_group_name'],
                                                       info['discord_channel_name'],
                                                       interaction.user.display_name))

    @discord.ui.button(label=messages.UNLINK_CANCEL_LABEL, style=discord.ButtonStyle.secondary)
    async def unlink_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content=messages.UNLINK_CANCELLED, view=None)


if __name__ == '__main__':
    client.run(config.get('discord_bot_token'))
