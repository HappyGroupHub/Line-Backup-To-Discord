import datetime
import math
import os
import time
import urllib.parse

import requests
import uvicorn
from discord import SyncWebhook, File
from fastapi import FastAPI
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, TextMessage, \
    ReplyMessageRequest, TemplateMessage, ConfirmTemplate, MessageAction, PushMessageRequest
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent, \
    VideoMessageContent, AudioMessageContent, StickerMessageContent, FileMessageContent, \
    LocationMessageContent
from pydantic import StrictStr

import download_manager
import line_sticker_downloader
import utilities as utils
from cache import sync_channels_cache

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

config = utils.read_config()
configuration = Configuration(access_token=config['line_channel_access_token'])
handler = WebhookHandler(config['line_channel_secret'])


def get_bot_name() -> str:
    """Get the bot name.

    :return str: The bot name.
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        profile = line_bot_api.get_bot_info()
        return profile.display_name


bot_name = get_bot_name()
dc_bot_invite_link = config['discord_bot_invite_link']


@app.post("/callback")
async def callback(request: Request):
    """Callback function for line webhook."""

    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = await request.body()

    # handle webhook body
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        if event.source.type == 'user':  # Exclude user messages, only process group messages
            return
        line_bot_api = MessagingApi(api_client)
        message_received = event.message.text
        group_id = event.source.group_id

        # Sync message to Discord
        if group_id in sync_channels_cache.line_group_ids:
            author = line_bot_api.get_group_member_profile(group_id, event.source.user_id)
            dc_channel_webhook = sync_channels_cache.get_dc_webhook_by_line_group_id(group_id)
            discord_webhook = SyncWebhook.from_url(dc_channel_webhook)
            discord_webhook.send(message_received, username=f"{author.display_name} - (Line訊息)",
                                 avatar_url=author.picture_url)

        # Handle commands messages
        if message_received == "!ID":
            reply_message = TextMessage(text=f"Group ID: {group_id}")
        elif message_received == f"@{bot_name} ":
            if group_id in sync_channels_cache.line_group_ids:
                reply_message = TextMessage(text="此群組已綁定")
            else:
                confirm_template = ConfirmTemplate(
                    text=StrictStr("請問你的 Discord 伺服器邀請備份機器人了嗎？"),
                    actions=[
                        MessageAction(label=StrictStr("還沒"),
                                      text=StrictStr("獲取 Discord 備份機器人邀請連結")),
                        MessageAction(label=StrictStr("已邀請"),
                                      text=StrictStr("確認並開始綁定"))
                    ])
                reply_message = TemplateMessage(altText="是否完成加入 Discord 機器人？",
                                                template=confirm_template)
        elif message_received == "獲取 Discord 備份機器人邀請連結":
            if dc_bot_invite_link:
                reply_message = TextMessage(text=dc_bot_invite_link)
            else:
                reply_message = TextMessage(text="架設者未公開 Discord Bot 邀請連結")
        elif message_received == "確認並開始綁定":
            if group_id in sync_channels_cache.line_group_ids:
                reply_message = TextMessage(text="此群組已綁定")
            else:
                group_name = line_bot_api.get_group_summary(group_id).group_name
                binding_code, expiration = utils.generate_binding_code(group_id, group_name)
                minutes_left = max(1, math.ceil((expiration - time.time()) / 60))
                reply_message = TextMessage(text=f"請至欲同步的Discord頻道中\n" \
                                                 f"\n----------------------\n" \
                                                 f"輸入以下指令來完成綁定\n" \
                                                 f"/link {binding_code}\n" \
                                                 f"----------------------\n" \
                                                 f"\n※注意※\n" \
                                                 f"此綁定碼僅能使用一次\n" \
                                                 f"並將於{minutes_left}分鐘後過期\n" \
                                                 f"過期前重複請求皆會取得同一組綁定碼")
        else:
            return
        line_bot_api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token, messages=[reply_message]))


@handler.add(MessageEvent, message=StickerMessageContent)
def handle_sticker_message(event):
    with ApiClient(configuration) as api_client:
        if event.source.type == 'user':  # Exclude user messages, only process group messages
            return
        line_bot_api = MessagingApi(api_client)
        group_id = event.source.group_id

        if group_id in sync_channels_cache.line_group_ids:
            subscribed_info = sync_channels_cache.get_info_by_line_group_id(group_id)
            author = line_bot_api.get_group_member_profile(group_id, event.source.user_id)
            is_animated = True if event.message.sticker_resource_type == 'ANIMATION' else False
            sticker_file = get_sticker_file(event.message.package_id, event.message.sticker_id,
                                            is_animated)
            if not sticker_file:
                return
            discord_webhook = SyncWebhook.from_url(subscribed_info['discord_channel_webhook'])
            discord_webhook.send(file=File(sticker_file),
                                 username=f"{author.display_name} - (Line訊息)",
                                 avatar_url=author.picture_url)
            download_manager.handle_sent_file(sticker_file, config)


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    with ApiClient(configuration) as api_client:
        if event.source.type == 'user':  # Exclude user messages, only process group messages
            return
        line_bot_api = MessagingApi(api_client)
        group_id = event.source.group_id
        if group_id in sync_channels_cache.line_group_ids:
            subscribed_info = sync_channels_cache.get_info_by_line_group_id(group_id)
            author = line_bot_api.get_group_member_profile(group_id, event.source.user_id)
            file_path = download_content(event.message.id, subscribed_info['folder_name'],
                                         'image')
            discord_webhook = SyncWebhook.from_url(subscribed_info['discord_channel_webhook'])
            discord_webhook.send(file=File(file_path),
                                 username=f"{author.display_name} - (Line訊息)",
                                 avatar_url=author.picture_url)
            download_manager.handle_sent_file(file_path, config)


@handler.add(MessageEvent, message=VideoMessageContent)
def handle_video_message(event):
    with ApiClient(configuration) as api_client:
        if event.source.type == 'user':  # Exclude user messages, only process group messages
            return
        line_bot_api = MessagingApi(api_client)
        group_id = event.source.group_id
        if group_id in sync_channels_cache.line_group_ids:
            subscribed_info = sync_channels_cache.get_info_by_line_group_id(group_id)
            author = line_bot_api.get_group_member_profile(group_id, event.source.user_id)
            file_path = download_content(event.message.id, subscribed_info['folder_name'],
                                         'video')
            discord_webhook = SyncWebhook.from_url(subscribed_info['discord_channel_webhook'])
            discord_webhook.send(file=File(file_path),
                                 username=f"{author.display_name} - (Line訊息)",
                                 avatar_url=author.picture_url)
            download_manager.handle_sent_file(file_path, config)


@handler.add(MessageEvent, message=AudioMessageContent)
def handle_video_message(event):
    with ApiClient(configuration) as api_client:
        if event.source.type == 'user':  # Exclude user messages, only process group messages
            return
        line_bot_api = MessagingApi(api_client)
        group_id = event.source.group_id
        if group_id in sync_channels_cache.line_group_ids:
            subscribed_info = sync_channels_cache.get_info_by_line_group_id(group_id)
            author = line_bot_api.get_group_member_profile(group_id, event.source.user_id)
            file_path = download_content(event.message.id, subscribed_info['folder_name'],
                                         'audio')
            discord_webhook = SyncWebhook.from_url(subscribed_info['discord_channel_webhook'])
            discord_webhook.send(file=File(file_path),
                                 username=f"{author.display_name} - (Line訊息)",
                                 avatar_url=author.picture_url)
            download_manager.handle_sent_file(file_path, config)


@handler.add(MessageEvent, message=FileMessageContent)
def handle_file_message(event):
    with ApiClient(configuration) as api_client:
        if event.source.type == 'user':  # Exclude user messages, only process group messages
            return
        line_bot_api = MessagingApi(api_client)
        group_id = event.source.group_id
        if group_id in sync_channels_cache.line_group_ids:
            subscribed_info = sync_channels_cache.get_info_by_line_group_id(group_id)
            author = line_bot_api.get_group_member_profile(group_id, event.source.user_id)
            file_path = download_content(event.message.id, subscribed_info['folder_name'],
                                         'file', file_name=event.message.file_name)
            discord_webhook = SyncWebhook.from_url(subscribed_info['discord_channel_webhook'])
            discord_webhook.send(file=File(file_path),
                                 username=f"{author.display_name} - (Line訊息)",
                                 avatar_url=author.picture_url)
            download_manager.handle_sent_file(file_path, config)


@handler.add(MessageEvent, message=LocationMessageContent)
def handle_location_message(event):
    with ApiClient(configuration) as api_client:
        if event.source.type == 'user':  # Exclude user messages, only process group messages
            return
        line_bot_api = MessagingApi(api_client)
        group_id = event.source.group_id
        if group_id in sync_channels_cache.line_group_ids:
            subscribed_info = sync_channels_cache.get_info_by_line_group_id(group_id)
            author = line_bot_api.get_group_member_profile(group_id, event.source.user_id)
            location = event.message
            if hasattr(location, 'address') and location.address:
                encoded_address = urllib.parse.quote(location.address)
                google_maps_link = f"https://www.google.com/maps/place/{encoded_address}"
            else:
                google_maps_link = (f"https://www.google.com/maps?q="
                                    f"{location.latitude},{location.longitude}")

            location_message = f"📍 {author.display_name}分享了位置訊息\n\n"
            if hasattr(location, 'title') and location.title:
                location_message += f"地點名稱: **{location.title}**\n"
            if hasattr(location, 'address') and location.address:
                location_message += f"詳細地址: [{location.address}]({google_maps_link})\n"
            else:
                location_message += google_maps_link

            discord_webhook = SyncWebhook.from_url(subscribed_info['discord_channel_webhook'])
            discord_webhook.send(location_message, username=f"{author.display_name} - (Line訊息)",
                                 avatar_url=author.picture_url)


def push_message(line_group_id: str, message: str):
    """Push a message to the specified LINE group.

    :param str line_group_id: LINE group ID.
    :param str message: Message to push.
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(PushMessageRequest(
            to=line_group_id, messages=[TextMessage(text=message)]))


def download_content(message_id: str, folder_name: str, content_type: str,
                     file_name: str = None) -> str:
    """Download content from LINE.

    :param str message_id: Message ID from LINE.
    :param str folder_name: The name of the folder you want to save files at.
    :param str content_type: File type, image, video, audio or file.
    :param str file_name: The file name you want to save as. Only used when content_type is file.
    :return str: The path of the downloaded file.
    """
    type_map = {
        'image': 'jpg',
        'video': 'mp4',
        'audio': 'm4a',
        'file': 'Get file name from args'
    }

    headers = {"Authorization": f"Bearer {config['line_channel_access_token']}"}
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    response = requests.get(url, headers=headers)
    download_path = f"./downloads/{folder_name}/"
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    if content_type == 'file' and file_name is not None:
        file_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{file_name}"
    else:
        file_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}.{type_map[content_type]}"

    with open(f"{download_path}{file_name}", 'wb') as fd:
        for chunk in response.iter_content():
            fd.write(chunk)
    return f"{download_path}{file_name}"


def get_sticker_file(sticker_package_id: int, single_sticker_id: int,
                     is_animation: bool) -> str | None:
    """Get the sticker file path.

    :param int sticker_package_id: Sticker package ID.
    :param int single_sticker_id: Sticker ID.
    :param bool is_animation: Whether the sticker is animation.
    :return str: The path of the sticker file. None if failed.
    """
    base_dir = "./downloads/stickers"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)

    package_exists = False
    sticker_package_dir = None
    for folder_name in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, folder_name)) and folder_name.startswith(
                f"{sticker_package_id}_"):
            package_exists = True
            sticker_package_dir = os.path.join(base_dir, folder_name)
            break
    if not package_exists:
        sticker_package_dir = line_sticker_downloader.download(sticker_package_id)
    # Mark the package as recently used, so size_limit mode removes it later than unused ones
    download_manager.mark_as_used(sticker_package_dir)

    for file_name in os.listdir(sticker_package_dir):
        if is_animation:
            if file_name.startswith(f"{single_sticker_id}.gif"):
                sticker_path = os.path.join(sticker_package_dir, file_name)
                return sticker_path
            continue
        else:
            if file_name.startswith(f"{single_sticker_id}.png"):
                sticker_path = os.path.join(sticker_package_dir, file_name)
                return sticker_path
            continue
    print(f"Sticker({sticker_package_id}): ID - {single_sticker_id} not found.")
    return None


if __name__ == '__main__':
    uvicorn.run(app, port=config['webhook_port'])
