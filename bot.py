import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import random
import requests
import os
import redis
import json

token = os.environ["TELEGRAM_TOKEN"]

REDIS_URL = os.environ.get("REDIS_URL")

bot = telebot.TeleBot(token)

# data = json.load(open('data.json', 'r', encoding = 'utf-8'))

data = {}

def save_data(key, value):
	if REDIS_URL:
		redis_db = redis.from_url(REDIS_URL)
		redis_db.set(key, value)
	else:
		data[key] = value

def load_data(key):
	if REDIS_URL:
		redis_db = redis.from_url(REDIS_URL)
		return redis_db.get(key)
	else:
		return data.get(key)

# def change_data():
#
# 	json.dump(
# 			data,
# 			open('data.json', 'w', encoding = 'utf-8'),
# 			indent = 2,
# 			ensure_ascii = False
# 	)


#Function that is used to create question output for user
def ans_out(dict):
	output = ''
	output += dict['question'] + '\n\n'

	for i in range(len(dict['answers'])):
		output += '{n}) '.format(n = i + 1)
		output += dict['answers'][i]
		output += '\n'

	output += '\n' + 'Номер ответа указывать не нужно'

	return output

def list_lines(list):
	output = ''
	count = 0
	for word in list:
		output += word
		count += 1
		if count <= len(list) - 1:
			output += '\n'

	return output

#Constants
MAIN_STATE = 'main'
IN_GAME_STATE = 'in_game'
DIFF_SET_STATE = 'set_diff'
API_URL = 'https://stepik.akentev.com/api/millionaire'
AV_COMMANDS = ['Спроси меня вопрос', 'Задать уровень сложности', 'Сбросить уровень сложности', 'Покажи счет', 'Очистить историю']
DIFF_LEVELS = {'1': 'Легкий', '2': 'Средний', '3': 'Сложный'}

#Keyboard constants
basic_markup, diff_markup = [ReplyKeyboardMarkup(
			resize_keyboard=True,
			one_time_keyboard=True,
			row_width=2
		) for x in range(2)]

basic_markup.add(*AV_COMMANDS)

diff_markup.add(*DIFF_LEVELS.values())


@bot.message_handler(commands=['start'])
def send_welcome(message):
	bot.reply_to(message, 'Это бот-игра в "Кто хочет стать миллионером?"\n\n Доступные команды:\n\n' + list_lines(AV_COMMANDS), reply_markup=basic_markup)


@bot.message_handler(func=lambda message: True)
def dispatcher(message):

	user_id = str(message.from_user.id)
	print(user_id)
	state = load_data('state:{}'.format(user_id))
	print(state)

	if state == None:
		state = MAIN_STATE
	print('going to dispatch')

	state = MAIN_STATE

	if state == MAIN_STATE:
		print('problem with handler x2')
		main_handler(message)
		print('message sent to main hanlder')
	elif state == IN_GAME_STATE:
		game_handler(message)
		print('sent to game handler')
	elif state == DIFF_SET_STATE:
		diff_handler(message)

def main_handler(message):

	user_id = str(message.from_user.id)

	if message.text == 'Привет':
		print('hello recieved')
		bot.reply_to(message,'Ну привет!', reply_markup = basic_markup)

	# this block uploads the question from API and sends user to an answer state
	elif message.text == 'Спроси меня вопрос':

		print('question identified')

		# if user has not set difficulty level, the questions will be easy by default
		if load_data('difficulty:{}'.format(user_id)) == None:
			load_question = json.dumps(requests.get(API_URL).json())
			save_data('current_question:{}'.format(user_id), load_question)
			print('question loaded')

		# otherwise the chosen difficulty level will be used via params
		else:
			load_difficulty = load_data('difficulty:{}'.format(user_id))
			load_question = json.dumps(requests.get(API_URL, params={'complexity': load_difficulty}).json())
			save_data('current_question:{}'.format(user_id), load_question)

		# right and wrong questions recived from API are saved in the database
		current_question = json.loads(load_data('current_question:{}'.format(user_id)))

		save_data('right_answer:{}'.format(user_id), current_question['answers'][0])

		current_question['wrong_answers'] = []
		for answer in current_question['answers'][1:]:
			current_question['wrong_answers'].append(answer)

		save_data('wrong_answers:{}'.format(user_id), json.dumps(current_question['wrong_answers']))

		# in the answer's list from API correct one is always the first
		# therefore we should shuffle them for output to user
		random.shuffle(current_question['answers'])
		#save_data('answers_output:{}'.format(user_id), current_question['answers'])

		ans_markup = ReplyKeyboardMarkup(
			resize_keyboard=True,
			one_time_keyboard=True,
			row_width=2
		)


		#keyboard_answers = load_data('answers_output:{}'.format(user_id))
		#for answer in keyboard_answers:
		for answer in current_question['answers']:
			ans_markup.add(KeyboardButton(answer))


		#special funciton is used to form output from question data
		bot.reply_to(message, ans_out(json.loads(load_data('current_question:{}'.format(user_id)))), reply_markup = ans_markup)

		ans_markup = ReplyKeyboardRemove()

		save_data('state:{}'.format(user_id), IN_GAME_STATE)
		print('sent to in game')

		#change_data()

	#Choice of difficulty level
	elif message.text == 'Задать уровень сложности':

		# requesting the current level to showcase
		# 'Легкий' is a default one
		if load_data('difficulty:{}'.format(user_id)) == None:
			current_diff_level = 'Легкий'
		else:
			current_diff_level = DIFF_LEVELS[load_data('difficulty:{}'.format(user_id))]

		bot.reply_to(message, 'Текущий уровень сложности: {}\n\nВыберите желаемый уровень сложности:\n\n'.format(current_diff_level) + list_lines(DIFF_LEVELS.values()), reply_markup = diff_markup)

		save_data('state:{}'.format(user_id), DIFF_SET_STATE)

		#change_data()

	elif message.text == 'Сбросить уровень сложности':

		if load_data('difficulty:{}'.format(user_id)) == None:
			bot.reply_to(message, 'Хм, похоже что вы его еще не устанавливали.\n\nУровень сложноси по умолчанию: Легкий', reply_markup = basic_markup)
		else:
			save_data('difficulty:{}'.format(user_id), None)
			bot.reply_to(message, 'Сделано!', reply_markup = basic_markup)

			#change_data()

	#Counter of wins and losses
	elif message.text == 'Покажи счет' or message.text == 'Покажи счёт':
		#if data['winloss'].get(user_id) == None:
		if load_data('wins:{}'.format(user_id)) == None and load_data('losses:{}'.format(user_id)) == None:
			bot.reply_to(message, 'Вы еще не играли :)', reply_markup = basic_markup)
		else: bot.reply_to(message, 'Победы: {w}, Поражения: {l}'.format(w = load_data('wins:{}'.format(user_id)), l = load_data('losses:{}'.format(user_id))), reply_markup = basic_markup)

	elif message.text == 'Очистить историю':
		if load_data('wins:{}'.format(user_id)) == None and load_data('losses:{}'.format(user_id)) == None:
			bot.reply_to(message, 'Вы еще не играли :)', reply_markup = basic_markup)
		else:
			save_data('wins:{}'.format(user_id), None)
			save_data('losses:{}'.format(user_id), None)
			bot.reply_to(message, 'Сделано! Забыли ;)', reply_markup = basic_markup)

			#change_data()

	else: bot.reply_to(message, 'Я тебя не понял', reply_markup = basic_markup)


def game_handler(message):

	user_id = str(message.from_user.id)

	print('arrived at game handler')


	if message.text	== load_data('right_answer:{}'.format(user_id)):
		bot.reply_to(message, 'Правильно!', reply_markup = basic_markup)

		if load_data('wins:{}'.format(user_id)) == None and load_data('losses:{}'.format(user_id)) == None:
			save_data('wins:{}'.format(user_id), '1')
			save_data('losses:{}'.format(user_id), '0')
		else:
			win_score = int(load_data('wins:{}'.format(user_id)))
			win_score += 1
			win_score = str(win_score)
			save_data('wins:{}'.format(user_id), win_score)


	elif message.text in json.loads(load_data('wrong_answers:{}'.format(user_id))):
		bot.reply_to(message, 'Неправильно :(', reply_markup = basic_markup)

		if load_data('wins:{}'.format(user_id)) == None and load_data('losses:{}'.format(user_id)) == None:
			save_data('losses:{}'.format(user_id), '1')
			save_data('wins:{}'.format(user_id), '0')
		else:
			loss_score = int(load_data('losses:{}'.format(user_id)))
			loss_score += 1
			loss_score = str(loss_score)
			save_data('losses:{}'.format(user_id), loss_score)


	else: bot.reply_to(message, 'Я тебя не понял', reply_markup = basic_markup)

	save_data('state:{}'.format(user_id), MAIN_STATE)
	print('game state finished, sent to dispatcher')

	#change_data()



def diff_handler(message):

	user_id = str(message.from_user.id)

	if message.text == 'Легкий' or message.text == 'Лёгкий':
		save_data('difficulty:{}'.format(user_id), '1')
		bot.reply_to(message, 'Готово!\n\nТеперь вы будете получать простые, и даже иногда шуточные вопросы :)', reply_markup = basic_markup)

	elif message.text == 'Средний':
		save_data('difficulty:{}'.format(user_id), '2')
		bot.reply_to(message, 'Готово!\n\nТеперь вы будете получать вопросы повышенной сложности.\n\nТак держать!', reply_markup = basic_markup)

	elif message.text == 'Сложный':
		save_data('difficulty:{}'.format(user_id), '3')
		bot.reply_to(message, 'Готово!\n\nТеперь вы будете получать самые сложные вопросы.\n\nУдачи!', reply_markup = basic_markup)

	save_data('state:{}'.format(user_id), MAIN_STATE)

	#change_data()


bot.polling()