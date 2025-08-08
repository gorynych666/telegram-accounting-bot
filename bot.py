import os
import re
import datetime
import logging
import calendar
import gspread
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)
from gspread_formatting import set_cell_format, CellFormat, Border, Color

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

logging.basicConfig(level=logging.INFO)

# Настройка Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# 12 столбцов таблицы
HEADERS = [
    "Дата", "Водитель (ФИО)", "Транспорт", "Номер транспорта", "Наименование груза",
    "Количество топлива", "Вид топлива", "Маршрут", "Расстояние (км)",
    "Машина (час)", "Остаток топлива", "Примечание"
]

# Формат границ для строки
border_format = CellFormat(
    borders={
        "top": Border("SOLID", Color(0, 0, 0)),
        "bottom": Border("SOLID", Color(0, 0, 0)),
        "left": Border("SOLID", Color(0, 0, 0)),
        "right": Border("SOLID", Color(0, 0, 0)),
    }
)

def get_month_sheet():
    now = datetime.datetime.now()
    month_title = now.strftime("%B").capitalize()  # Пример: "August"
    try:
        return client.open_by_key(GOOGLE_SHEET_ID).worksheet(month_title)
    except gspread.exceptions.WorksheetNotFound:
        sheet = client.open_by_key(GOOGLE_SHEET_ID).add_worksheet(title=month_title, rows="1000", cols="20")
        sheet.append_row(HEADERS)
        return sheet

def format_date(raw_date):
    try:
        return datetime.datetime.strptime(raw_date, "%d.%m.%Y").strftime("%d.%m.%Y")
    except ValueError:
        return datetime.datetime.now().strftime("%d.%m.%Y")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    values = text.split()

    # Автозаполнение текущей даты, если она не указана
    date_regex = r"^\d{2}\.\d{2}\.\d{4}$"
    if values and re.match(date_regex, values[0]):
        date = format_date(values.pop(0))
    else:
        date = format_date("")

    # Дополнить недостающие элементы пустыми значениями
    while len(values) < 11:
        values.append("")

    row = [date] + values[:11]  # Итого 12 значений

    sheet = get_month_sheet()
    sheet.append_row(row)

    # Применить границы к последней строке
    last_row_index = len(sheet.get_all_values())
    for col in range(1, 13):  # Столбцы A–L (1–12)
        set_cell_format(sheet, f"{chr(64 + col)}{last_row_index}", border_format)

    await update.message.reply_text("✅ Данные успешно добавлены в таблицу!")

if __name__ == "__main__":
    from telegram.ext import Application

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    webhook_url = f"{RENDER_EXTERNAL_URL}"
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=webhook_url,
    )