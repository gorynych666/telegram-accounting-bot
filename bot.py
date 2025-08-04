import os
import json
import base64
import datetime
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
encoded_credentials = os.environ.get("GOOGLE_SERVICE_ACCOUNT_B64")

if not TELEGRAM_TOKEN or not SPREADSHEET_ID or not RENDER_EXTERNAL_URL or not encoded_credentials:
    raise ValueError("Не все переменные окружения заданы")

# Декодируем ключ из base64 и парсим JSON
try:
    decoded_json = base64.b64decode(encoded_credentials).decode("utf-8")
    creds_dict = json.loads(decoded_json)
except Exception as e:
    raise ValueError(f"Ошибка при декодировании GOOGLE_SERVICE_ACCOUNT_B64: {e}")

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

# Получить лист текущего месяца
def get_current_month_sheet():
    month_name = datetime.datetime.now().strftime("%B")
    try:
        return client.open_by_key(SPREADSHEET_ID).worksheet(month_name)
    except gspread.WorksheetNotFound:
        raise ValueError(f"Лист с названием '{month_name}' не найден в таблице.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message_text = update.message.text.strip()
        parts = message_text.split(" ")

        komu = parts[0] if len(parts) > 0 else ""
        vid = parts[1] if len(parts) > 1 else ""
        kolvo = parts[2] if len(parts) > 2 else ""
        date = parts[3] if len(parts) > 3 and "." in parts[3] else datetime.datetime.now().strftime("%d.%m.%Y")
        primechanie = " ".join(parts[4:]) if len(parts) > 4 else ""

        if len(parts) > 3 and "." not in parts[3]:
            primechanie = " ".join(parts[3:])

        sheet = get_current_month_sheet()
        sheet.append_row([komu, vid, kolvo, date, primechanie])

        await update.message.reply_text("✅ Данные успешно добавлены.")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text(f"⚠️ Ошибка: {e}")

# Запуск через webhook (Render)
if __name__ == "__main__":
    from telegram.ext import Application

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Настройка webhook
    webhook_url = f"{RENDER_EXTERNAL_URL}"
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=webhook_url,
    )