import telebot
import datetime
from telebot import types
from db import BotDB
from dotenv import load_dotenv
import os

load_dotenv()

PROXY_URL = "http://proxy.server:3128"
BotDB = BotDB('finance.db')
bot = telebot.TeleBot(token=os.environ.get('TOKEN'), )


def button_start():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = types.KeyboardButton('Запустить')
    markup.add(start_button)
    return markup


@bot.message_handler(func=lambda message: True)
def start(message):
    if message.text == 'Запустить' or message.text == '/start' or message.text == 'Назад':
        if not BotDB.user_exists(message.from_user.id):
            BotDB.add_user(message.from_user.id, message.from_user.first_name)
        markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        answer1 = types.KeyboardButton('➕Доход')
        answer2 = types.KeyboardButton('➖Расход')
        answer3 = types.KeyboardButton('📊Статистика доходов / расходов')
        answer4 = types.KeyboardButton('🛑Выйти')
        markup1.add(answer1, answer2, answer3, answer4)
        if message.text == 'Назад':
            bot.send_message(message.chat.id, 'Выберите тему для записи снова'.format(message.from_user),
                             reply_markup=markup1)
        else:
            bot.send_message(message.chat.id, 'Добро пожаловать, {0.first_name} , в CashFlowBot!\n\n'
                                              'Выберите тему для записи'.format(message.from_user), reply_markup=markup1)
        bot.register_next_step_handler(message, found)


@bot.message_handler(content_types=['text'])
def found(message):
    if message.text == '➕Доход':
        entering_amount_income(message)
    elif message.text == '➖Расход':
        choosing_topics(message)
    elif message.text == '📊Статистика доходов / расходов':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton('За день')
        item2 = types.KeyboardButton('За неделю')
        item3 = types.KeyboardButton('За месяц')
        item4 = types.KeyboardButton('За все время')
        item5 = types.KeyboardButton('Назад')
        markup.add(item1, item2, item3, item4, item5)
        bot.send_message(message.chat.id, 'За какой период времени требуется статистика?'.format(message.from_user), reply_markup=markup)
        bot.register_next_step_handler(message, statistic)
    elif message.text == '🛑Выйти':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        start_button = types.KeyboardButton('Запустить')
        markup.add(start_button)
        bot.send_message(message.chat.id, 'Увидимся снова!', reply_markup=button_start())


@bot.message_handler(content_types=['text'])
def choosing_topics(message):
    result_flow = BotDB.get_categories_flow()
    if len(result_flow):
        answer_to_flow = f'💸Основные категории расходов💸\n\n'
        for row in result_flow:
            answer_to_flow += f"{row[0]}"
            answer_to_flow += f" - {row[1]}\n"
        number2 = bot.send_message(message.chat.id, 'Введите номер категории Ваших расходов')
        bot.register_next_step_handler(number2, entering_amount_flow)
        return bot.send_message(message.from_user.id, answer_to_flow)


@bot.message_handler(content_types=['text'])
def entering_amount_flow(message):
    name_cat_flow = BotDB.get_name_categories_flow(message.text)
    if name_cat_flow:
        id_cat = BotDB.get_category_id(name_cat_flow[0][0])
        name_flow = name_cat_flow[0][0]
        type_operation = 'Расход'
        amount_flow = bot.send_message(message.chat.id, 'Введите потраченную сумму')
        bot.register_next_step_handler(amount_flow, add_note_to_db_flow, id_cat, type_operation)
    else:
        bot.send_message(message.from_user.id, 'Неверный ввод категории! Попробуйте снова')
        bot.register_next_step_handler(message, entering_amount_flow)


@bot.message_handler(content_types=['text'])
def entering_amount_income(message):
    type_operation = 'Доход'
    amount_income = bot.send_message(message.chat.id, 'Введите полученную сумму')
    bot.register_next_step_handler(amount_income, add_note_to_db_income, type_operation)


@bot.message_handler(content_types=['text'])
def add_note_to_db_flow(message, id_cat, type_oper):
    if message.text.isalpha() or int(message.text) < 0:
        bot.send_message(message.from_user.id, 'Ошибка при вводе суммы! Попробуйте снова')
        bot.register_next_step_handler(message, add_note_to_db_flow, id_cat, type_oper)
    else:
        BotDB.add_note(message.from_user.id, type_oper, message.text, id_cat[0][0])
        answer = bot.send_message(message.chat.id, 'Данные успешно сохранены!')
        bot.register_next_step_handler(answer, found)


@bot.message_handler(content_types=['text'])
def add_note_to_db_income(message, type_oper):
    if message.text.isalpha() or int(message.text) < 0:
        bot.send_message(message.from_user.id, 'Ошибка при вводе суммы! Попробуйте снова')
        bot.register_next_step_handler(message, add_note_to_db_income, type_oper)
    else:
        BotDB.add_note(message.from_user.id, type_oper, message.text, None)
        answer = bot.send_message(message.chat.id, 'Данные успешно сохранены!')
        bot.register_next_step_handler(answer, found)


@bot.message_handler(content_types=['text'])
def statistic(message):
    records = ''
    if message.text == 'За день':
        records = BotDB.get_statistic(message.from_user.id, 'day')
    elif message.text == 'За неделю':
        records = BotDB.get_statistic(message.from_user.id, 'week')
    elif message.text == 'За месяц':
        records = BotDB.get_statistic(message.from_user.id, 'month')
    elif message.text == 'За все время':
        records = BotDB.get_statistic(message.from_user.id, 'for all time')

    if len(records):
        sum_flow = 0
        sum_income = 0
        answer = f"🕘 История операций {message.text}\n\n"
        for r in records:
            answer += ('➕' if r[2] == 'Доход' else '➖') + r[2]
            answer += f" - {r[3]} руб."
            date_str = r[4]
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f%z")
            formatted_date = date_obj.strftime("%d %B %Y %H:%M")
            answer += f" Дата: {formatted_date}\n"
            if r[2] == 'Доход':
                sum_income += r[3]
            elif r[2] == 'Расход':
                sum_flow += r[3]
        answer += f"\nИтого потрачено {message.text}: \nДоход - {sum_income} руб. \nРасход - {sum_flow} руб."
        bot.send_message(message.chat.id, answer)
        bot.register_next_step_handler(message, statistic)
    elif message.text == 'Назад':
        start(message)
    else:
        bot.send_message(message.chat.id, 'Данные не обнаружены!')
        bot.register_next_step_handler(message, statistic)


bot.polling(none_stop=True)