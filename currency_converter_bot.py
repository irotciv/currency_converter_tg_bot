import re
import zipfile
from io import BytesIO

import pandas as pd
import requests
import telebot
from currency_converter import CurrencyConverter
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip'
response = requests.get(url)
zip_file = zipfile.ZipFile(BytesIO(response.content))
zip_file.extractall()
zip_file.close()

df = pd.read_csv('eurofxref.csv')
df[' '] = 39.42
df.rename(columns={' ': 'UAH'}, inplace=True)
df.to_csv('eurofxref.csv', index=False)

c = CurrencyConverter('eurofxref.csv')
description = ('Choose what you want to do:\n/convert - to convert currency\n'
               '/rate - to see the specific currency rate you want\n\nAllowed currency: ' + ', '.join(c.currencies))


def convert(message):
    data = str(message.text.upper()).replace(' ', '').split(',')
    if len(data) == 2:
        data.append(data[1])
    try:
        result = c.convert(float(data[0]), data[1], data[2])
        rate = c.convert(1, data[1], data[2])
        bot.send_message(message.chat.id, f'The rate: {rate}\nThe result: {result}')
    except Exception as e:
        bot.send_message(message.chat.id, e)


def chart(message):
    data = str(message.text.upper()).replace(' ', '').split(',')
    if len(data) == 1:
        data.append(data[0])
    try:
        bot.send_message(message.chat.id, f'The rate: {c.convert(1, data[0], data[1])}')
    except Exception as e:
        bot.send_message(message.chat.id, e)


@bot.message_handler(commands=['start'])
def start(message):
    last_name = f' {message.from_user.last_name}' if message.from_user.last_name is not None else ''
    bot.send_message(message.chat.id, f'Hello, {message.from_user.first_name}{last_name}!\n{description}')


@bot.message_handler(commands=['convert'])
def converter(message):
    bot.send_message(message.chat.id, 'Enter the amount, from and to currency like this: 10.10,USD,EUR')
    bot.register_next_step_handler(message, convert)


@bot.message_handler(commands=['rate'])
def get_chart(message):
    bot.send_message(message.chat.id, 'Enter from and to currency like this: USD,EUR')
    bot.register_next_step_handler(message, chart)


@bot.message_handler()
def default(message):
    text = message.text
    if re.match('[0-9.]+,[a-zA-Z, ]+', text):
        convert(message)
    elif re.match('[a-zA-Z, ]', text):
        chart(message)
    else:
        bot.send_message(message.chat.id, description + '\n\nOr check if the data is correct')


bot.polling(none_stop=True)
