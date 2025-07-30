import os
import datetime
import logging
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_FILE = "telegramfuelbot-7da908eba21b.json"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

print("Загруженный TELEGRAM_TOKEN:", TELEGRAM_TOKEN)
print("Бот запущен...")

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_FILE, scope)
client = gspread.authorize(credentials)

# Словарь русских месяцев
russian_months = {
    "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель",
    "05": "Май", "06": "Июнь", "07": "Июль", "08": "Август",
    "09": "Сентябрь", "10": "Октябрь", "11": "Ноябрь", "12": "Декабрь"
}

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()

    if len(parts) < 3:
        await update.message.reply_text("❗ Пожалуйста, введите хотя бы Кому, Вид и Кол-во.")
        return

    кому = parts[0]
    вид = parts[1]
    количество = parts[2]

    # Определяем дату
    if len(parts) >= 4 and "." in parts[3]:
        дата = parts[3]
        примечание = " ".join(parts[4:]) if len(parts) > 4 else ""
    else:
        дата = datetime.datetime.now().strftime('%d.%m.%Y')
        примечание = " ".join(parts[3:]) if len(parts) > 3 else ""

    # Получаем название месяца на русском
    try:
        day, month, year = дата.split(".")
    except ValueError:
        await update.message.reply_text("⚠️ Неверный формат даты. Используйте ДД.ММ.ГГГГ.")
        return

    month_name_ru = russian_months.get(month)
    if not month_name_ru:
        await update.message.reply_text("⚠️ Не удалось определить месяц из даты.")
        return

    # Открытие или создание листа
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        worksheet = spreadsheet.worksheet(month_name_ru)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=month_name_ru, rows="1000", cols="10")
        worksheet.append_row(["Кому", "Вид", "Кол-во", "Дата", "Примечание"])

    # Добавление строки
    row = [кому, вид, количество, дата, примечание]
    worksheet.append_row(row)

    await update.message.reply_text(f"✅ Данные добавлены на вкладку «{month_name_ru}».")

# Запуск бота
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())