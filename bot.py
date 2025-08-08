import logging
import os
import re
from datetime import datetime

from dotenv import load_dotenv
from gspread_formatting import CellFormat, set_cell_format, Border
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)
import calendar

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Данные из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

# Авторизация Google
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
client = gspread.authorize(credentials)

# Названия столбцов (на русском)
HEADERS = [
    "Дата", "Водитель (ФИО)", "Транспорт", "Номер транспорта",
    "Наименование груза", "Количество топлива", "Вид топлива",
    "Маршрут", "Расстояние (км)", "Машина (час)", "Остаток топлива", "Примечание"
]

# Функция: автоформат
def apply_borders(ws, row_index: int):
    cell_range = f"A{row_index}:L{row_index}"
    border_format = CellFormat(
        borders={
            "top": Border("SOLID"),
            "bottom": Border("SOLID"),
            "left": Border("SOLID"),
            "right": Border("SOLID")
        }
    )
    set_cell_format(ws, cell_range, border_format)

# Функция: получение/создание листа по текущему месяцу
def get_or_create_month_worksheet():
    now = datetime.now()
    sheet_name = now.strftime("%B")
    sheet_name_ru = {
        'January': 'Январь', 'February': 'Февраль', 'March': 'Март',
        'April': 'Апрель', 'May': 'Май', 'June': 'Июнь',
        'July': 'Июль', 'August': 'Август', 'September': 'Сентябрь',
        'October': 'Октябрь', 'November': 'Ноябрь', 'December': 'Декабрь'
    }.get(sheet_name, sheet_name)

    try:
        worksheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name_ru)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = client.open_by_key(SPREADSHEET_ID).add_worksheet(title=sheet_name_ru, rows="1000", cols="12")
        worksheet.append_row(HEADERS)

    return worksheet

# Парсинг сообщения
def parse_message(message: str):
    parts = message.strip().split()

    if len(parts) < 11:
        raise ValueError("Недостаточно данных. Минимум 11 элементов.")

    main_data = parts[:11]
    notes = " ".join(parts[11:]) if len(parts) > 11 else ""
    today = datetime.today().strftime("%d.%m.%Y")
    return [today] + main_data + [notes]

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message.text
        data = parse_message(message)
        worksheet = get_or_create_month_worksheet()
        worksheet.append_row(data)
        apply_borders(worksheet, len(worksheet.get_all_values()))
        await update.message.reply_text("✅ Данные успешно добавлены.")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

# Запуск бота
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()