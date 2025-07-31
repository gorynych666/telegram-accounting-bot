import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import gspread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Загружаем переменные окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Авторизация в Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
raw_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
creds_dict = json.loads(raw_credentials)

# Исправляем переносы в ключе
if "private_key" in creds_dict:
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_ID)

# Получаем название текущего месяца
month_title = datetime.now().strftime('%B').capitalize()
worksheet = sheet.worksheet(month_title)

# Асинхронная обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    parts = text.split()

    # Добавляем дату (если она не указана вручную)
    try:
        datetime.strptime(parts[3], "%d.%m.%Y")
        data = parts
    except (IndexError, ValueError):
        today = datetime.now().strftime("%d.%m.%Y")
        data = parts[:3] + [today] + parts[3:]

    # Делаем длину списка = 5, дополняем пустыми значениями
    while len(data) < 5:
        data.append("")

    worksheet.append_row(data)
    await update.message.reply_text("✅ Данные успешно добавлены!")

# Запуск бота
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()