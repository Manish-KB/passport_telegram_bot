import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image
import io
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime

user_input = None
driver = None

def stop(update, context):
    context.bot.send_message(chat_id=context.user_data['current_chat_id'], text="Bot Stopped")
    sys.exit()


def start(update, context):
    global driver
    buttons = [['/start','/stop']]
    # Create the keyboard markup
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! \nLoading the captcha for you ⏳", reply_markup=keyboard)

    chrome_options = Options()
    chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(options=chrome_options)

    driver.get('https://passportindia.gov.in/AppOnlineProject/online/apptAvailStatus')

    dropdown = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'pboId'))).click()
    option_xpath = "//option[@value='5']"
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, option_xpath))).click()

    captcha_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'captcha')))
    screenshot = captcha_element.screenshot_as_png
    image = Image.open(io.BytesIO(screenshot)).convert("RGB")
    jpeg_image = io.BytesIO()
    image.save(jpeg_image, format='JPEG')

    jpeg_image.seek(0)

    context.user_data['current_chat_id'] = update.effective_chat.id

    context.bot.send_photo(chat_id=context.user_data['current_chat_id'], photo=jpeg_image)
    context.bot.send_message(chat_id=context.user_data['current_chat_id'], text="Please enter the captcha code.")
    context.user_data['user_input_handler'] = MessageHandler(Filters.text & ~Filters.command, handle_user_input)
    context.dispatcher.add_handler(context.user_data['user_input_handler'])

def handle_user_input(update, context):
    global user_input
    user_input = update.message.text
    context.dispatcher.remove_handler(context.user_data['user_input_handler'])
    submit_captcha_and_process(context)

def submit_captcha_and_process(context: CallbackContext):
    global user_input, driver

    if user_input is not None:
        if user_input.lower()=="stop":
            context.bot.send_message(chat_id=context.user_data['current_chat_id'], text="Bot Stopped")
            sys.exit()
        captcha_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'test123')))
        captcha_input.send_keys(user_input)

        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "bt")))
        button.click()

        table_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/table/tbody/tr/td/table/tbody/tr[1]/td/div/table/tbody/tr[6]/td/table/tbody/tr/td[2]/form/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[10]/td/table/tbody/tr[3]/td/table')))
        first_row = table_element.find_element(By.XPATH, ".//tr[2]")

        if 'Lalbagh' in first_row.text:
            if 'Normal' in first_row.text:
                appointments_released = first_row.find_element(By.XPATH, ".//td[5]").text
                
                input_date_str = appointments_released.replace("Available for ", "")
                input_date = datetime.strptime(input_date_str, "%d/%m/%Y")
                day_of_week = input_date.strftime("%A")
                appointments_released=appointments_released.replace("Available for ", "Available for\n")
                message = appointments_released + " " + day_of_week
                context.bot.send_message(chat_id=context.user_data['current_chat_id'], text=message)
                
            else:
                context.bot.send_message(chat_id=context.user_data['current_chat_id'], text="Error")
        else:
            context.bot.send_message(chat_id=context.user_data['current_chat_id'], text="Error")

updater = Updater(token='6961596587:AAHvJX5O3MI1tr-FlDVHncfLlpNew83smvI', use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('stop', stop))
updater.start_polling()
updater.idle()
