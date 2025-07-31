import os
import json
import datetime
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
raw_credentials = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

if not TELEGRAM_TOKEN or not SPREADSHEET_ID or not raw_credentials:
    raise ValueError("Одна или несколько переменных окружения не заданы")

# Преобразуем JSON-строку в словарь
creds_dict = json.loads(raw_credentials)

# Авторизация в Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

# Получаем название листа по текущему месяцу
def get_current_month_sheet():
    month_name = datetime.datetime.now().strftime("%B")
    try:
        return client.open_by_key(SPREADSHEET_ID).worksheet(month_name)
    except gspread.WorksheetNotFound:
        raise ValueError(f"Лист с названием '{month_name}' не найден в таблице.")

# Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message_text = update.message.text.strip()
        parts = message_text.split(" ")

        # Определяем значения
        komu = parts[0] if len(parts) > 0 else ""
        vid = parts[1] if len(parts) > 1 else ""
        kolvo = parts[2] if len(parts) > 2 else ""
        date = parts[3] if len(parts) > 3 and "." in parts[3] else datetime.datetime.now().strftime("%d.%m.%Y")
        primechanie = " ".join(parts[4:]) if len(parts) > 4 else ""

        # Если дата указана в виде 4-го элемента, учитываем это
        if len(parts) > 3 and "." in parts[3]:
            primechanie = " ".join(parts[4:])
        elif len(parts) > 3:
            primechanie = " ".join(parts[3:])

        # Открываем таблицу
        sheet = get_current_month_sheet()

        # Добавляем строку
        sheet.append_row([komu, vid, kolvo, date, primechanie])

        await update.message.reply_text("✅ Данные успешно добавлены.")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text(f"⚠️ Произошла ошибка: {e}")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()