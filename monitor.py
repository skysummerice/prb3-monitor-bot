import time
import requests
import json
import threading
import telebot

chat_id = None

def get_data(endpoint_url):
    try:
        response = requests.get(endpoint_url)
        data = response.json()
        parsed_data = []
        state_count = {}
        for worker in data['workers']:
            worker_state = worker['state']
            worker_id = worker['worker']['id']
            worker_name = worker['worker']['name']
            worker_stake = worker['worker']['stake']
            if worker_state in state_count:
                state_count[worker_state] += 1
            else:
                state_count[worker_state] = 1

            if worker_state != 'Working':
                worker_data = {
                    'worker_id': worker_id,
                    'worker_name': worker_name,
                    'state': worker_state,
                    'stake': worker_stake
                }
                parsed_data.append(worker_data)
        return state_count, parsed_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

def send_updates(bot, chat_id, endpoint_url):
    while True:
        state_count, data = get_data(endpoint_url)
        if data:
            for worker_data in data:
                message = f"Worker ID: {worker_data['worker_id']}\n" \
                          f"Worker Name: {worker_data['worker_name']}\n" \
                          f"State: {worker_data['state']}\n" \
                          f"Stake: {worker_data['stake']}"
                bot.send_message(chat_id, message)
        time.sleep(60)

def register(bot, message):
    global chat_id
    chat_id = message.chat.id
    bot.reply_to(message, f'Registered with chat id {chat_id}')

def getworkerinfo(bot, message):
    with open('config.json') as config_file:
        config = json.load(config_file)
    endpoint_url = config['endpoint_url']
    state_count, data = get_data(endpoint_url)
    if state_count is not None:
        state_message = "Worker state count:\n" + "\n".join(f"{state}: {count}" for state, count in state_count.items())
        bot.send_message(chat_id, state_message)

def main():
    with open('config.json') as config_file:
        config = json.load(config_file)
    bot_token = config['bot_token']
    endpoint_url = config['endpoint_url']
    global chat_id
    chat_id = config['chat_id']

    bot = telebot.TeleBot(bot_token)

    bot.message_handler(commands=['register'])(lambda message: register(bot, message))
    bot.message_handler(commands=['getworkerinfo'])(lambda message: getworkerinfo(bot, message))

    update_thread = threading.Thread(target=send_updates, args=(bot, chat_id, endpoint_url))
    update_thread.start()

    bot.polling(none_stop=True)

if __name__ == '__main__':
    main()
