"""All user-facing messages of the LINE and Discord bots.

Keep the wording here so it can be reviewed and edited in one place.
"""

BOT_TITLE = "LINE ➵ Discord 訊息備份機器人"
SUPPORTED_TYPES = "文字、LINE 表情貼、圖片、影片、語音、檔案、貼圖和位置"

# ---------------------------------------------------------------------------------------------
# LINE
# ---------------------------------------------------------------------------------------------
LINE_JOIN_GREETING = (
    f"大家好！我是 {BOT_TITLE} 👋\n"
    f"\n"
    f"我可以把這個群組的訊息即時備份到 Discord 頻道，"
    f"支援{SUPPORTED_TYPES}。\n"
    f"\n"
    f"想開始備份的話，在群組裡 @我 一下，我會帶你完成設定。"
)

# Confirm template: text max 240 chars, button labels max 12 chars
LINE_MENU_ALT_TEXT = "開始備份前，請先邀請 Discord 備份機器人"
LINE_MENU_TEXT = "要開始備份這個群組，需要先把 Discord 備份機器人邀請到你的伺服器。\n請問邀請好了嗎？"
LINE_MENU_NOT_YET_LABEL = "還沒，給我連結"
LINE_MENU_NOT_YET_DISPLAY = "請給我 Discord 機器人的邀請連結"
LINE_MENU_READY_LABEL = "邀請好了"
LINE_MENU_READY_DISPLAY = "邀請好了，開始綁定"


def line_already_bound(discord_channel_name: str) -> str:
    return (f"這個群組已經在備份中了 ✅\n"
            f"\n"
            f"Discord 頻道：#{discord_channel_name}\n"
            f"\n"
            f"如果要停止備份，請到該 Discord 頻道輸入 /unlink。")


def line_invite_link(invite_link: str) -> str:
    return (f"這是 Discord 備份機器人的邀請連結：\n"
            f"{invite_link}\n"
            f"\n"
            f"邀請到伺服器後，再 @我 一次就可以開始綁定。")


def line_invite_link_unavailable(hosted_by: str) -> str:
    return (f"這個機器人的架設者沒有公開 Discord 邀請連結，"
            f"請直接聯絡架設者（{hosted_by}）取得。")


def line_binding_code_instructions(minutes_left: int) -> str:
    return (f"綁定碼產生好了！\n"
            f"請到想要備份的 Discord 頻道，輸入下一則訊息中的指令（長按即可複製）。\n"
            f"\n"
            f"・綁定碼只能使用一次\n"
            f"・{minutes_left} 分鐘內有效，期間重複申請會拿到同一組")


def line_binding_command(binding_code: int) -> str:
    return f"/link {binding_code}"


def line_group_id(group_id: str) -> str:
    return f"這個群組的 ID：\n{group_id}"


def line_link_success(line_group_name: str, discord_channel_name: str) -> str:
    return (f"✅ 綁定成功，開始備份！\n"
            f"\n"
            f"LINE 群組：{line_group_name}\n"
            f"Discord 頻道：#{discord_channel_name}\n"
            f"\n"
            f"從現在起，這個群組的{SUPPORTED_TYPES}訊息都會自動備份到 Discord。")


def line_unlink_success(line_group_name: str, discord_channel_name: str, user_name: str) -> str:
    return (f"已停止備份\n"
            f"\n"
            f"LINE 群組：{line_group_name}\n"
            f"Discord 頻道：#{discord_channel_name}\n"
            f"操作者：{user_name}（Discord）\n"
            f"\n"
            f"之後的訊息不會再備份。想重新開始的話，@我 就可以再次綁定。")


# ---------------------------------------------------------------------------------------------
# Discord - backed up messages
# ---------------------------------------------------------------------------------------------
def discord_backup_username(line_display_name: str) -> str:
    return f"{line_display_name} - (Line訊息)"


def discord_location(title: str | None, address: str | None, maps_link: str,
                     latitude: float, longitude: float) -> str:
    lines = [f"📍 **{title}**" if title else "📍 **位置訊息**"]
    lines.append(address if address else f"{latitude}, {longitude}")
    # <> around the link stops Discord from showing a big map preview
    lines.append(f"[在 Google 地圖開啟](<{maps_link}>)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------
# Discord - slash commands
# ---------------------------------------------------------------------------------------------
COMMAND_DESCRIPTIONS = {
    'about': "查看機器人資訊和這個頻道的備份狀態",
    'help': "查看機器人的使用方式",
    'link': "用綁定碼把這個頻道和 LINE 群組綁定，開始備份",
    'unlink': "解除這個頻道和 LINE 群組的綁定，停止備份",
}
LINK_CODE_DESCRIPTION = "在 LINE 群組 @機器人 取得的 6 位數綁定碼"


def about_description(help_mention: str) -> str:
    return (f"把 LINE 群組的訊息即時備份到 Discord 的免費服務。\n"
            f"由 [樂弟](https://github.com/HappyGroupHub) 開發並開源，歡迎大家一起維護。\n"
            f"\n"
            f"輸入 {help_mention} 查看使用方式。")


ABOUT_STATUS_FIELD = "這個頻道的備份狀態"
ABOUT_NOT_BOUND = "尚未綁定任何 LINE 群組"


def about_bound(line_group_name: str) -> str:
    return f"備份中：LINE 群組 **{line_group_name}**"


def help_description(about: str, link: str, unlink: str) -> str:
    return (f"**開始備份**\n"
            f"`1.` 把 LINE 備份機器人加進 LINE 群組\n"
            f"`2.` 在 LINE 群組裡 @機器人，依照指示取得綁定碼\n"
            f"`3.` 在想要備份的 Discord 頻道輸入 {link} 加上綁定碼\n"
            f"\n"
            f"**指令**\n"
            f"{about}｜查看機器人資訊和這個頻道的備份狀態\n"
            f"{link}｜用綁定碼把這個頻道和 LINE 群組綁定\n"
            f"{unlink}｜解除綁定，停止備份\n"
            f"\n"
            f"支援備份{SUPPORTED_TYPES}訊息。")


LINK_INVALID_CODE = ("找不到這組綁定碼，請確認有沒有輸入錯誤。\n"
                     "綁定碼可以在 LINE 群組裡 @機器人 取得。")
LINK_EXPIRED_CODE = "這組綁定碼已經過期了，請回到 LINE 群組再 @機器人 一次，取得新的綁定碼。"
LINK_WRONG_CHANNEL = "只能在伺服器的文字頻道使用 /link 喔。"
LINK_MISSING_PERMISSION = ("我沒有這個頻道的「管理 Webhook」權限，所以沒辦法開始備份。\n"
                           "請在頻道設定中給我這個權限，再試一次 /link。")


def link_channel_already_bound(line_group_name: str) -> str:
    return (f"這個頻道已經在備份 LINE 群組「{line_group_name}」了。\n"
            f"如果要改成備份其他群組，請先用 /unlink 解除目前的綁定。")


LINK_SUCCESS_TITLE = "✅ 綁定成功，開始備份！"
LINK_SUCCESS_DESCRIPTION = f"這個 LINE 群組的新訊息會自動備份到這裡，支援{SUPPORTED_TYPES}。"
LINK_SUCCESS_FOOTER = "使用 /unlink 可以隨時停止備份"
FIELD_LINE_GROUP = "LINE 群組"
FIELD_DISCORD_CHANNEL = "Discord 頻道"

UNLINK_NOT_BOUND = "這個頻道目前沒有綁定任何 LINE 群組。"


def unlink_confirm(line_group_name: str) -> str:
    return (f"確定要停止備份 LINE 群組「{line_group_name}」嗎？\n"
            f"解除後，新訊息就不會再備份到這個頻道，已經備份的訊息會保留。")


UNLINK_CONFIRM_LABEL = "解除綁定"
UNLINK_CANCEL_LABEL = "取消"
UNLINK_DONE = "已解除綁定。"
UNLINK_CANCELLED = "已取消，備份會繼續進行。"
UNLINK_TIMED_OUT = "太久沒有回應，已自動取消，備份會繼續進行。"
UNLINK_SUCCESS_TITLE = "已停止備份"
UNLINK_SUCCESS_DESCRIPTION = "想重新開始的話，在 LINE 群組裡 @機器人 就可以再次綁定。"


def unlink_success_footer(user_name: str) -> str:
    return f"操作者：{user_name}"
