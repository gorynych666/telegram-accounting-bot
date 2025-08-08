import logging
import os
from datetime import datetime

import gspread
from dotenv import load_dotenv
from gspread_formatting import CellFormat, Border, set_frozen
from gspread_formatting import set_format
from gspread_formatting import Color
from gspread_formatting import CellFormat, format_cell_range, Border, Color
from gspread_formatting import Border
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Connect to Google Sheets
gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
sheet = gc.open_by_key(SPREADSHEET_ID)

# Define month mapping
MONTHS = {
    "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель",
    "05": "Май", "06": "Июнь", "07": "Июль", "08": "Август",
    "09": "Сентябрь", "10": "Октябрь", "11": "Ноябрь", "12": "Декабрь"
}

# Border formatting
border = Border("SOLID", Color(0, 0, 0, 1))
cell_format = CellFormat(
    borders={'top': border, 'bottom': border, 'left': border, 'right': border}
)


def add_borders(worksheet, row_number):
    cell_range = f"A{row_number}:L{row_number}"
    set_cell_format(worksheet, cell_range, cell_format)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()

    if len(parts) < 11:
        await update.message.reply_text("Ошибка: слишком мало данных. Нужно минимум 11 полей.")
        return

    driver = parts[0]
    vehicle = parts[1]
    model = parts[2]
    plate = parts[3]
    cargo = parts[4]
    fuel_qty = parts[5]
    fuel_type = parts[6]
    route = parts[7]
    distance = parts[8]
    machine_hours = parts[9]
    fuel_left = parts[10]
    note = " ".join(parts[11:]) if len(parts) > 11 else ""

    # Current date
    today = datetime.now()
    date_str = today.strftime("%d.%m.%Y")
    month_tab = MONTHS[today.strftime("%m")]

    try:
        worksheet = sheet.worksheet(month_tab)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=month_tab, rows="100", cols="12")

    row = [date_str, driver, vehicle, model, plate, cargo, fuel_qty,
           fuel_type, route, distance, machine_hours, fuel_left, note]

    try:
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        row_num = len(worksheet.get_all_values())
        add_borders(worksheet, row_num)
        await update.message.reply_text("✅ Данные успешно добавлены.")
    except Exception as e:
        logging.error(f"Ошибка при добавлении строки: {e}")
        await update.message.reply_text("❌ Ошибка при добавлении данных в таблицу.")


if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    app.add_handler(handler)
    app.run_polling()