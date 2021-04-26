import telebot
from telebot import types
from telebot.types import Message, CallbackQuery
from data import db_session
from data.users import User
import pandas as pd
import sqlite3
from random import choice, randint

db_session.global_init("db/stats.db")
TOKEN = '1769856429:AAEJnlhzBihddISNsQX5RebX5h2FxnGR3oo'
BUTTONS = ["/правила", "/статистика", '/ТОП', '/играть']
bot = telebot.TeleBot(TOKEN)
MOVES = [['+1', '+2', '+3', '+4', '+2', '+3'], ['*2', '*2', '*2', '*3', '*4']]
DATASET = {}
GAME = {}
STOP = False
x = set()


@bot.message_handler(commands=["start", "help", "home"])
def start(message: Message):  # встречаем, рассказываем правила
    hello_text = """Привет, это EgeGame
    Я здесь чтобы ты мог лучше разобраться в 19-21 задании егэ по информатике
    Или можешь просто проверить свои познания в теории ИГР"""
    bot.send_message(message.from_user.id, hello_text)

    if not message.from_user.username:
        bot.send_message(message.from_user.id, "У вас нет имени пользователя @username, создайте его "
                                               "в настройках телеграмма и перезапустите бота")
        return
    markup = types.ReplyKeyboardMarkup()  # инициализируем начальные кнопки
    butts = []
    texts = BUTTONS[:]
    for text in texts:
        butts.append(types.KeyboardButton(text))
    markup.add(*butts)
    bot.send_message(message.from_user.id, "начнаем?", reply_markup=markup)


@bot.message_handler(commands=["правила"])
def rules(message: Message):
    try:
        rule_text = """Есть два игрока: Петя и Ваня, Петя ходит Первыи, Ваня Второй.
    Перед ними лежат от 2 кучи камгей
    Есть два действия либо +n либо *m
    Мы можем выполнить это действие с любой из куч, 
    После чего ход перейдёт к другому игроку
    Побеждает тот у кого первого сумма камней будет >= S"""
        bot.send_message(message.from_user.id, rule_text)
        rule_text = """После нажатия на кнопку играть, 
    вам будет предложен выбор, между рейтинговой игрой и без
    В рейтинговой игре, параметры подбираются случайно, и ваши игры попадают в статистику
    В обычной игры, вы саме можете выбирать все параметры и ваши победы не будут учитываться.
    Во время рейтинговой игры нельзя вводить команды, 
    можно нажимать только на предложенные, не то бот засчитает поражение"""
        bot.send_message(message.from_user.id, rule_text)
        markup = types.ReplyKeyboardMarkup()  # инициализируем начальные кнопки
        butts = []
        texts = BUTTONS[:]
        for text in texts:
            butts.append(types.KeyboardButton(text))
        markup.add(*butts)
        bot.send_message(message.from_user.id, "начинаем?", reply_markup=markup)
    except Exception as s:
        print('непредвиденная ошибка', s)
        bot.send_message(message.from_user.id, 'непредвиденная ошибка, попробуйте заново')
        start(message)


@bot.message_handler(commands=["ТОП"])
def top(message: Message):
    con = sqlite3.connect("db/stats.db")
    df = pd.read_sql("SELECT * from users", con)
    print(df)
    df = df.loc[df['result_game'] == 1]
    df = df.groupby('name').count()
    df = df.loc[:, ['name', 'result_game']]
    df.sort_values(by=['result_game'])
    bot.send_message(message.from_user.id, text=str(df))


@bot.message_handler(commands=["статистика"])
def stats(message: Message):
    con = sqlite3.connect("db/stats.db")
    df = pd.read_sql("SELECT * from users", con)
    df = df.loc[df['id_player'] == message.from_user.id]
    df = df.loc[:, ['name',
                    'result_game',
                    'game_date']]
    bot.send_message(message.from_user.id, text=str(df))


@bot.message_handler(commands=["играть"])
def game(message: Message):
    try:
        GAME[message.from_user.id] = True
        move1 = choice(MOVES[0])
        move2 = choice(MOVES[1])
        a, b = randint(5, 20), randint(5, 20)
        s = eval('({}+{}{}){}+50'.format(a, b, move1, move2))
        DATASET[message.from_user.id] = {'a': a, 'b': b, 'move1': move1, 'move2': move2, 's': s, 'sel': ''}
        text_mes = """1 куча: {}
    2 куча: {}
    Варианты действий: {} {}
    Итоговая сумма: {}""".format(a, b, move1, move2, s)
        bot.send_message(message.from_user.id, text_mes, reply_markup=types.ReplyKeyboardRemove())
        markup = types.InlineKeyboardMarkup(row_width=2)
        texts = ['куча1 - {}'.format(a), 'куча2 - {}'.format(b)]
        button1 = types.InlineKeyboardButton(texts[0], callback_data='first')
        button2 = types.InlineKeyboardButton(texts[1], callback_data='second')

        markup.add(button1, button2)
        bot.send_message(message.from_user.id, 'Выберите кучу', reply_markup=markup)
    except Exception as s:
        print('непредвиденная ошибка', s)
        bot.send_message(message.from_user.id, 'непредвиденная ошибка, попробуйте заново')
        start(message)


@bot.callback_query_handler(func=lambda call: True)
def callback(call: CallbackQuery):
    try:
        if call.message and GAME[call.from_user.id]:
            if call.from_user.id in DATASET:
                data = DATASET[call.from_user.id]
            else:
                data = {}
            if call.data == 'first':
                markup = types.InlineKeyboardMarkup(row_width=2)
                a, b = data['move1'], data['move2']
                button1 = types.InlineKeyboardButton(a, callback_data='plus')
                button2 = types.InlineKeyboardButton(b, callback_data='umnozit')
                data['sel'] = '1'
                markup.add(button1, button2)
                bot.send_message(call.from_user.id, 'Выберите действие', reply_markup=markup)
            elif call.data == 'second':
                markup = types.InlineKeyboardMarkup(row_width=2)
                a, b = data['move1'], data['move2']
                button1 = types.InlineKeyboardButton(a, callback_data='plus')
                button2 = types.InlineKeyboardButton(b, callback_data='umnozit')
                data['sel'] = '2'
                markup.add(button1, button2)
                bot.send_message(call.from_user.id, 'Выберите действие', reply_markup=markup)
            elif call.data == 'plus':
                if data['sel'] == '1':
                    data['a'] = eval('{}{}'.format(data['a'], data['move1']))
                    if data['a'] + data['b'] >= data['s']:
                        bot.send_message(call.from_user.id, 'Вы выиграли, поздравляю')
                        GAME[call.from_user.id] = False
                        add_play(1, call)
                        markup = types.ReplyKeyboardMarkup()  # инициализируем начальные кнопки
                        butts = []
                        texts = BUTTONS[:]
                        for text in texts:
                            butts.append(types.KeyboardButton(text))
                        markup.add(*butts)
                        bot.send_message(call.from_user.id, "Что будем делать дальше?", reply_markup=markup)
                    else:
                        my_step(call)
                else:
                    data['b'] = eval('{}{}'.format(data['b'], data['move1']))
                    if data['a'] + data['b'] >= data['s']:
                        bot.send_message(call.from_user.id, 'Вы выиграли, поздравляю')
                        GAME[call.from_user.id] = False
                        add_play(1, call)
                        markup = types.ReplyKeyboardMarkup()  # инициализируем начальные кнопки
                        butts = []
                        texts = BUTTONS[:]
                        for text in texts:
                            butts.append(types.KeyboardButton(text))
                        markup.add(*butts)
                        bot.send_message(call.from_user.id, "Что будем делать дальше?", reply_markup=markup)
                    else:
                        my_step(call)
            elif call.data == 'umnozit':
                if data['sel'] == '2':
                    data['b'] = eval('{}{}'.format(data['b'], data['move2']))
                    if data['a'] + data['b'] >= data['s']:
                        bot.send_message(call.from_user.id, 'Вы выиграли, поздравляю')
                        GAME[call.from_user.id] = False
                        add_play(1, call)
                        markup = types.ReplyKeyboardMarkup()  # инициализируем начальные кнопки
                        butts = []
                        texts = BUTTONS[:]
                        for text in texts:
                            butts.append(types.KeyboardButton(text))
                        markup.add(*butts)
                        bot.send_message(call.from_user.id, "Что будем делать дальше?", reply_markup=markup)
                    else:
                        my_step(call)
                else:
                    data['a'] = eval('{}{}'.format(data['a'], data['move2']))
                    if data['a'] + data['b'] >= data['s']:
                        bot.send_message(call.from_user.id, 'Вы выиграли, поздравляю')
                        GAME[call.from_user.id] = False
                        add_play(1, call)
                        markup = types.ReplyKeyboardMarkup()  # инициализируем начальные кнопки
                        butts = []
                        texts = BUTTONS[:]
                        for text in texts:
                            butts.append(types.KeyboardButton(text))
                        markup.add(*butts)
                        bot.send_message(call.from_user.id, "Что будем делать дальше?", reply_markup=markup)
                    else:
                        my_step(call)
    except Exception as s:
        print('непредвиденная ошибка', s)
        bot.send_message(call.from_user.id, 'непредвиденная ошибка, попробуйте заново')
        start(call)


def my_step(message):
    try:
        global x, STOP
        x = set()
        STOP = False
        data = DATASET[message.from_user.id]
        lucky_step([data['a'], data['b']], message)
        converter(message)
        a, b, move1, move2, s, sep = [data[i] for i in data]
        text_mes = """1 куча: {}
        2 куча: {}
        Варианты действий: {} {}
        Итоговая сумма: {}""".format(a, b, move1, move2, s)
        bot.send_message(message.from_user.id, text_mes, reply_markup=types.ReplyKeyboardRemove())
        if data['a'] + data['b'] >= data['s']:
            bot.send_message(message.from_user.id, 'Я выиграл, это было понятно в начале игры')
            GAME[message.from_user.id] = False
            add_play(0, message)

            markup = types.ReplyKeyboardMarkup()  # инициализируем начальные кнопки
            butts = []
            texts = BUTTONS[:]
            for text in texts:
                butts.append(types.KeyboardButton(text))
            markup.add(*butts)
            bot.send_message(message.from_user.id, "Что будем делать дальше?", reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup(row_width=2)
            texts = ['куча1 - {}'.format(a), 'куча2 - {}'.format(b)]
            button1 = types.InlineKeyboardButton(texts[0], callback_data='first')
            button2 = types.InlineKeyboardButton(texts[1], callback_data='second')

            markup.add(button1, button2)
            bot.send_message(message.from_user.id, 'Выберите кучу', reply_markup=markup)
    except Exception as s:
        print('непредвиденная ошибка', s)
        bot.send_message(message.from_user.id, 'непредвиденная ошибка, попробуйте заново')
        start(message)


def converter(message):
    try:
        d = {'0': 'a', '1': 'b'}
        if list(x) != []:
            name_a, b = choice(list(x)).split()
            a = d[name_a]
            data = DATASET[message.from_user.id]
            DATASET[message.from_user.id][a] = eval('{}{}'.format(data[a], b))
            bot.send_message(message.from_user.id, 'Я выберу {}ую кучу, и действие {}'.format(int(name_a) + 1, b))
    except Exception as s:
        print('непредвиденная ошибка', s)
        bot.send_message(message.from_user.id, 'непредвиденная ошибка, попробуйте заново')
        start(message)


def lucky_step(box, message, k=0, steps=None):
    try:
        global x, STOP
        if steps is None:
            steps = []
        data = DATASET[message.from_user.id]
        win = data['s']
        boxes = [data['a'], data['b']]
        if not STOP:
            if sum(box) >= win or k == 5:
                if k < 5 and k % 2 == 1:
                    if steps != []:
                        x = {steps}
                    STOP = True
                elif k == 5:
                    x.add(steps)

            else:
                for i in range(len(box)):
                    for func in [data['move1'], data['move2']]:
                        lucky_step(box=[eval('{}{}'.format(boxes[i], func)), boxes[(i + 1) % len(box)]],
                                   message=message,
                                   k=k + 1,
                                   steps=str(i) + ' ' + func)
    except Exception as s:
        print('непредвиденная ошибка', s)
        bot.send_message(message.from_user.id, 'непредвиденная ошибка, попробуйте заново')
        start(message)


def add_play(bool, messege: Message):
    user = User()
    user.name = messege.from_user.username
    user.id_player = messege.from_user.id
    user.result_game = bool
    db_sess = db_session.create_session()
    db_sess.add(user)
    db_sess.commit()


bot.polling()
