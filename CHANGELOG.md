# Changelog

## v0.1.1 - LINE Emoji Support & Friendlier Messages

### ✨ New Features

- **LINE emoji support:** Text messages with LINE emojis are now backed up with the emoji images. A message with only
  emojis is sent as images, just like a sticker, and animated emojis become GIFs.
- **Downloads folder management:** The new `downloads_mode` setting in `config.yml` keeps the `downloads` folder under
  control. Keep everything (`unlimited`, default), keep it under a size limit (`size_limit`), or remove files right
  after they're backed up (`instant_burn`).
- **Welcome message:** The bot introduces itself when it's added to a LINE group.

### 💬 Friendlier Interactions

- Rewrote every LINE and Discord message to be clearer, with proper line breaks and the full list of supported message
  types.
- Tag the bot anywhere in a message (`@bot hello`) to start binding, not only with the exact `@bot` text.
- The binding code is sent as its own message, so it's easy to copy.
- The menu buttons in LINE no longer post command text into the group.
- `/link` and `/unlink` results are shown as embeds, `/unlink` cleans up its webhook and confirmation buttons.
- Clear error messages when `/link` is used in a thread, in a channel that's already bound, or without the
  `Manage Webhooks` permission.

### 🐛 Bug Fixes

- Binding codes are now really single-use, and asking for a code repeatedly returns the same one.
- `/about` no longer fails when the invite links in `config.yml` are left empty.
- `/link` no longer crashes before any binding code has been generated.
- `/link` and `/unlink` still respond when the LINE group can't be reached.

### 🔧 Under the Hood

- Upgraded to Python 3.13 and updated every dependency to the latest version.
- Animated stickers are converted with Pillow instead of the unmaintained apnggif.
- Added a bilingual (English / 繁體中文) README.

### ⬆️ Upgrading From v0.1.0

- **Windows release:** Replace `LineBackupToDiscord.exe` with the new one. Keep your own `config.yml`,
  `sync_channels.json` and `downloads` folder, and don't overwrite your `config.yml` with the one in the zip.
- **Running from source:** Delete the `.venv` folder before running `run.bat` / `run.sh`, so the environment is rebuilt
  with Python 3.13.
- `config.yml` from v0.1.0 still works. Add `downloads_mode` and `downloads_max_size_mb` only if you want to limit the
  `downloads` folder, see the README.

---

### ✨ 新功能

- **支援 LINE 表情貼：** 含有 LINE 表情貼的文字訊息會連同表情貼圖片一起備份。只有表情貼的訊息會像貼圖一樣以圖片傳送，動態表情貼則會轉為 GIF。
- **管理 downloads 資料夾：** `config.yml` 新增 `downloads_mode` 設定，可以選擇全部保留 (`unlimited`，預設)、限制資料夾大小
  (`size_limit`)，或是在備份完成後立即刪除檔案 (`instant_burn`)。
- **歡迎訊息：** 機器人被加入 LINE 群組時會自我介紹。

### 💬 更友善的互動

- 重新撰寫所有 LINE 與 Discord 訊息，內容更清楚、換行更整齊，並列出完整的支援訊息種類。
- 在訊息中任意位置 tag 機器人 (例如 `@機器人 你好`) 就能開始綁定，不再需要只輸入 `@機器人`。
- 綁定碼會單獨傳送一則訊息，方便長按複製。
- LINE 的選單按鈕不會再把指令文字發送到群組中。
- `/link` 及 `/unlink` 的結果改以嵌入訊息 (embed) 顯示，`/unlink` 完成後會清除 webhook 及確認按鈕。
- 在討論串中使用 `/link`、頻道已經綁定，或缺少「管理 Webhook」權限時，會顯示清楚的錯誤訊息。

### 🐛 錯誤修正

- 綁定碼現在真正只能使用一次，重複申請也會取得同一組綁定碼。
- `config.yml` 的邀請連結留空時，`/about` 不會再失敗。
- 尚未產生過任何綁定碼時，`/link` 不會再當機。
- 無法連線到 LINE 群組時，`/link` 及 `/unlink` 仍會正常回應。

### 🔧 其他更新

- 升級至 Python 3.13，並將所有套件更新至最新版本。
- 動態貼圖改用 Pillow 轉換，取代已停止維護的 apnggif。
- 新增中英雙語 README。

### ⬆️ 從 v0.1.0 升級

- **Windows 執行檔版本：** 用新的 `LineBackupToDiscord.exe` 取代舊的即可。請保留你自己的 `config.yml`、`sync_channels.json` 及
  `downloads` 資料夾，不要用壓縮檔中的 `config.yml` 覆蓋你的設定檔。
- **從原始碼執行：** 執行 `run.bat` / `run.sh` 前請先刪除 `.venv` 資料夾，讓環境以 Python 3.13 重新建立。
- v0.1.0 的 `config.yml` 可以繼續使用。只有想限制 `downloads` 資料夾大小時，才需要加上 `downloads_mode` 及
  `downloads_max_size_mb`，請參考 README。

## v0.1.0 - First Release!

First release, see the [release notes](https://github.com/HappyGroupHub/Line-Backup-To-Discord/releases/tag/v0.1.0).
