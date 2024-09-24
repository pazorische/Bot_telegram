import telebot
import requests
import time
from telebot import types

bot = telebot.TeleBot('')
TELEGRAM_BOT_TOKEN = ''


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hi, my name is ServiceNow test bot. I can create and check the incidents")


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Hi, my name is ServiceNow test bot. I can create and check the incidents")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "I don't get you, write /help.")


bot.polling(none_stop=True)
