import os
import json
import datetime
import logging
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Загрузка переменных окружения из .env (локально)
load_dotenv()

# Получаем токен из переменной среды
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
print(f"Загруженный TELEGRAM_TOKEN: {TELEGRAM_TOKEN}")

# Авторизация Google Sheets через переменную среды с JSON-ключом
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_json = os.getenv("GOOGLE_CREDS_JSON")
creds_dict = json.loads(creds_json)
credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)

client = gspread.authorize(credentials)

# Определение названия таблицы по текущему месяцу
def get_sheet():
    month_name = datetime.datetime.now().strftime("%B")  # Например: 'July'
    try:
        sheet = client.open("telegram-bot-data").worksheet(month_name)
    except gspread.exceptions.WorksheetNotFound:
        sheet = client.open("telegram-bot-data").add_worksheet(title=month_name, rows="1000", cols="5")
        sheet.append_row(["Кому", "Вид", "Кол-во", "Дата", "Примечания"])
    return sheet

# Обработка входящего сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    parts = text.split()
    
    кому = parts[0] if len(parts) > 0 else ""
    вид = parts[1] if len(parts) > 1 else ""
    количество = parts[2] if len(parts) > 2 else ""
    дата = parts[3] if len(parts) > 3 and "." in parts[3] else datetime.datetime.now().strftime("%d.%m.%Y")
    примечание = " ".join(parts[4:]) if len(parts) > 4 else ""
    
    if "." not in дата:
        примечание = " ".join(parts[3:])
        дата = datetime.datetime.now().strftime("%d.%m.%Y")

    sheet = get_sheet()
    sheet.append_row([кому, вид, количество, дата, примечание])
    
    await update.message.reply_text("✅ Данные успешно записаны!")

# Запуск Telegram-бота
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()