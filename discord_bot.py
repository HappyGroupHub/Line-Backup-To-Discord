import time

import discord
from discord import app_commands
from discord.ext import commands

import line_bot
import utilities as utils
from cache import sync_channels_cache

config = utils.read_config()

client = commands.Bot(command_prefix="!", intents=discord.Intents.default())


async def on_ready():
    """Initialize discord bot."""
    print("Bot is ready.")
    try:
        synced = await client.tree.sync()
        print(f"Synced {synced} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@app_commands.describe()
async def about(interaction: discord.Interaction):
    subscribed_info = sync_channels_cache.get_info_by_dc_channel_id(interaction.channel.id)
    if subscribed_info:
        sync_info = f"=======================================\n" \
                    f"Discord頻道：{subscribed_info['discord_channel_name']}\n" \
                    f"Line群組      ：{subscribed_info['line_group_name']}\n" \
                    f"=======================================\n"
    else:
        sync_info = f"尚未與任何 LINE 群組連動備份！\n"
    all_commands = await client.tree.fetch_commands()
    help_command = discord.utils.get(all_commands, name="help")
    embed_message = discord.Embed(title="LINE ➵ Discord 訊息備份機器人",
                                  description=f"一個協助你備份 LINE 訊息的免費服務\n\n"
                                              f"目前同步備份的服務：\n"
                                              f"{sync_info}\n"
                                              f"此專案由 [樂弟](https://github.com/HappyGroupHub) 開發，"
                                              f"並開源歡迎所有人共\n同維護。"
                                              f"你可以使用指令 {help_command.mention} 了解如何\n使用此機器人\n",
                                  color=0x2ecc71)
    embed_message.set_author(name=client.user.name, icon_url=client.user.avatar)
    embed_message.add_field(name="作者", value="LD", inline=True)
    embed_message.add_field(name="架設者", value=config['bot_hosted_by'], inline=True)
    embed_message.add_field(name="版本", value="v0.1.0", inline=True)
    await interaction.response.send_message(embed=embed_message, view=AboutCommandView())


class AboutCommandView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=0)
        github_row = 0
        if 'line_bot_invite_link' in config:
            self.add_item(discord.ui.Button(label="Line Bot邀請連結",
                                            url=config['line_bot_invite_link'],
                                            style=discord.ButtonStyle.link,
                                            emoji="💬"))
            github_row = 1
        if 'discord_bot_invite_link' in config:
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
    embed_message = discord.Embed(title="LINE ➵ Discord 訊息備份機器人",
                                  description=f"`1.` {about_command.mention}｜關於機器人\n"
                                              f"> 查看機器人的詳細資訊, 以及目前連動備份中的服務\n\n"
                                              f"`2.` {link_command.mention}｜綁定Line群組並開始備份\n"
                                              f"> 邀請Line Bot至群組中並直接 tag(@) 該機器人\n"
                                              f"> 獲得Discord綁定碼後即可使用此指令連動備份\n\n"
                                              f"`3.` {unlink_command.mention}｜解除Line群組綁定並取消備份\n"
                                              f"> 解除與Line群組的綁定, 並取消連動備份服務\n\n",
                                  color=0x2ecc71)
    embed_message.set_author(name=client.user.name, icon_url=client.user.avatar)
    await interaction.response.send_message(embed=embed_message)


@app_commands.describe(binding_code="輸入你的綁定碼")
async def link(interaction: discord.Interaction, binding_code: int):
    binding_info = utils.get_binding_code_info(binding_code)
    if binding_info is None:
        reply_message = "綁定失敗, 該綁定碼輸入錯誤或格式不正確, 請再試一次."
        await interaction.response.send_message(reply_message, ephemeral=True)
    elif binding_info['expiration'] < time.time():
        utils.remove_binding_code(binding_code)
        reply_message = "綁定失敗, 此綁定碼已逾5分鐘內無使用而過期, 請再試一次."
        await interaction.response.send_message(reply_message, ephemeral=True)
    else:
        webhook = await interaction.channel.create_webhook(name="Line訊息同步")
        utils.add_new_sync_channel(binding_info['line_group_id'], binding_info['line_group_name'],
                                   interaction.channel.id, interaction.channel.name, webhook.url)
        utils.remove_binding_code(binding_code)
        push_message = f"綁定成功！\n" \
                       f"     ----------------------\n" \
                       f"    |    LINE ➵ Discord   |\n" \
                       f"    |    訊息備份機器人   |\n" \
                       f"     ----------------------\n\n" \
                       f"Discord頻道：{interaction.channel.name}\n" \
                       f"Line群組      ：{binding_info['line_group_name']}\n" \
                       f"===================\n" \
                       f"目前支援連動備份：文字訊息、圖片、影片、音訊"
        reply_message = f"**【LINE ➵ Discord 訊息備份機器人 - 綁定成功！】**\n\n" \
                        f"Discord頻道：{interaction.channel.name}\n" \
                        f"Line群組      ：{binding_info['line_group_name']}\n" \
                        f"========================================\n" \
                        f"目前支援連動備份：文字訊息、圖片、影片、音訊"
        line_bot.push_message(binding_info['line_group_id'], push_message)
        await interaction.response.send_message(reply_message)


@app_commands.describe()
async def unlink(interaction: discord.Interaction):
    subscribed_info = sync_channels_cache.get_info_by_dc_channel_id(interaction.channel.id)
    if not subscribed_info:
        reply_message = "此頻道並未綁定任何Line群組！"
        await interaction.response.send_message(reply_message, ephemeral=True)
    else:
        reply_message = f"**【LINE ➵ Discord - 解除連動備份！】**\n\n" \
                        f"Discord頻道：{subscribed_info['discord_channel_name']}\n" \
                        f"Line群組      ：{subscribed_info['line_group_name']}\n" \
                        f"========================================\n" \
                        f"請問確定要解除同步嗎？"
        await interaction.response.send_message(reply_message,
                                                view=UnlinkConfirmation(subscribed_info),
                                                ephemeral=True)


class UnlinkConfirmation(discord.ui.View):
    def __init__(self, subscribed_info):
        super().__init__(timeout=20)
        self.subscribed_info = subscribed_info

    @discord.ui.button(label="⛓️ 確認解除同步", style=discord.ButtonStyle.danger)
    async def unlink_confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        utils.remove_sync_channel(discord_channel_id=self.subscribed_info['discord_channel_id'])
        push_message = f"已解除同步！\n" \
                       f"     ----------------------\n" \
                       f"    |    LINE ➵ Discord   |\n" \
                       f"    |    訊息備份機器人   |\n" \
                       f"     ----------------------\n\n" \
                       f"Discord頻道：{self.subscribed_info['discord_channel_name']}\n" \
                       f"Line群組      ：{self.subscribed_info['line_group_name']}\n" \
                       f"===================\n" \
                       f"執行者：{interaction.user.display_name}\n"
        reply_message = f"**【LINE ➵ Discord 訊息備份機器人 - 已解除同步！】**\n\n" \
                        f"Discord頻道：{self.subscribed_info['discord_channel_name']}\n" \
                        f"Line群組      ：{self.subscribed_info['line_group_name']}\n" \
                        f"========================================\n" \
                        f"執行者：{interaction.user.display_name}\n"
        self.stop()
        line_bot.push_message(self.subscribed_info['line_group_id'], push_message)
        await interaction.response.send_message(reply_message)

    @discord.ui.button(label="取消操作", style=discord.ButtonStyle.primary)
    async def unlink_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        reply_message = "操作已取消！"
        self.stop()
        await interaction.response.send_message(reply_message, ephemeral=True)


if __name__ == '__main__':
    client.run(config.get('discord_bot_token'))
