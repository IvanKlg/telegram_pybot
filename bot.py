import telebot

import random

import requests

import os

token = os.environ["TELEGRAM_TOKEN"]

#TOKEN = '1654695250:AAFB7nE0Jw9-P4PUDnO8l1Jo5Wgp_oFyM5w'

bot = telebot.TeleBot(token)

#Словари
states = {}
current_queston = {}
difficulty = {}
winloss = {}


#Константы
MAIN_STATE = 'main'
IN_GAME_STATE = 'in_game'
DIFF_SET_STATE = 'set_diff'
API_URL = 'https://stepik.akentev.com/api/millionaire'



@bot.message_handler(commands=['start'])
def send_welcome(message):
	bot.reply_to(message, 'Это бот-игра в "Кто хочет стать миллионером?"\n\n Доступные команды:\n\n'
						  + 'Cпроси меня вопрос\n'
						  + 'Задать уровень сложности\n'
						  + 'Сбросить уровень сложности\n'
						  + 'Покажи счет\n'
						  + 'Очистить историю')

@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == MAIN_STATE)
def main_handler(message):
	if message.text == 'Привет':
		bot.reply_to(message,'Ну привет!')

	elif message.text == 'Спроси меня вопрос':

		if difficulty.get(message.from_user.id) == None:

			current_queston[message.from_user.id] = requests.get(API_URL).json()

		else: current_queston[message.from_user.id] = requests.get(API_URL, params={'complexity': difficulty[message.from_user.id]}).json()

		current_queston[message.from_user.id]['right_answer'] = current_queston[message.from_user.id]['answers'][0]

		current_queston[message.from_user.id]['wrong_answers'] = []

		for answer in current_queston[message.from_user.id]['answers'][1:]:

			current_queston[message.from_user.id]['wrong_answers'].append(answer)

		random.shuffle(current_queston[message.from_user.id]['answers'])

		bot.reply_to(message, current_queston[message.from_user.id]['question'] + '\n\n'
					 + '1) ' + current_queston[message.from_user.id]['answers'][0] + '\n'
					 + '2) ' + current_queston[message.from_user.id]['answers'][1] + '\n'
					 + '3) ' + current_queston[message.from_user.id]['answers'][2] + '\n'
					 + '4) ' + current_queston[message.from_user.id]['answers'][3] + '\n\n'
					 'Номер ответа указывать не нужно'
					 )

		states[message.from_user.id] = IN_GAME_STATE

	#Выбор уровня сложности
	elif message.text == 'Задать уровень сложности':
		bot.reply_to(message, 'Выберите уровень сложности:\n\nЛегкий\nСредний\nСложный')

		states[message.from_user.id] = DIFF_SET_STATE

	elif message.text == 'Сбросить уровень сложности':

		if difficulty.get(message.from_user.id) == None:
			bot.reply_to(message, 'Хм, похоже что вы его еще не устанавливали.')
		else:
			del difficulty[message.from_user.id]
			bot.reply_to(message, 'Сделано!')

	#Счетчик побед и поражений
	elif message.text == 'Покажи счет' or message.text == 'Покажи счёт':
		if winloss.get(message.from_user.id) == None:
			bot.reply_to(message, 'Вы еще не играли :)')
		else: bot.reply_to(message, 'Победы: {w}, Поражения: {l}'.format(w = winloss[message.from_user.id]['win'], l = winloss[message.from_user.id]['loss']))

	elif message.text == 'Очистить историю':
		if winloss.get(message.from_user.id) == None:
			bot.reply_to(message, 'Вы еще не играли :)')
		else:
			del winloss[message.from_user.id]
			bot.reply_to(message, 'Сделано! Забыли ;)')

	else: bot.reply_to(message, 'Я тебя не понял')


@bot.message_handler(func=lambda message: states.get(message.from_user.id) == IN_GAME_STATE)
def game_handler(message):


	if message.text	== current_queston[message.from_user.id]['right_answer']:
		bot.reply_to(message, 'Правильно!')

		if winloss.get(message.from_user.id) == None:
			winloss[message.from_user.id] = {'win': 1, 'loss': 0}
		else:
			winloss[message.from_user.id]['win'] += 1


	elif message.text in current_queston[message.from_user.id]['wrong_answers']:
		bot.reply_to(message, 'Неправильно :(')

		if winloss.get(message.from_user.id) == None:
			winloss[message.from_user.id] = {'win': 0, 'loss': 1}
		else:
			winloss[message.from_user.id]['loss'] += 1


	else: bot.reply_to(message, 'Я тебя не понял')


	states[message.from_user.id] = MAIN_STATE

@bot.message_handler(func=lambda message: states.get(message.from_user.id) == DIFF_SET_STATE)
def game_handler(message):

	if message.text == 'Легкий' or message.text == 'Лёгкий':
		difficulty[message.from_user.id] = '1'
		bot.reply_to(message, 'Готово! Теперь вы будете получать простые, и даже иногда шуточные вопросы :)')


	elif message.text == 'Средний':
		difficulty[message.from_user.id] = '2'
		bot.reply_to(message, 'Готово! Теперь вы будете получать вопросы повышенной сложности.\nТак держать!')

	elif message.text == 'Сложный':
		difficulty[message.from_user.id] = '3'
		bot.reply_to(message, 'Готово! Теперь вы будете получать самые сложные вопросы.\nУдачи!')

	states[message.from_user.id] = MAIN_STATE



bot.polling()