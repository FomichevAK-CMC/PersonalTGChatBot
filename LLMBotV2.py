import telebot
from openai import OpenAI
import time
from configparser import ConfigParser

config = ConfigParser()
config.read("config.cfg")
base_url = config.get('setup', 'base_url')
api_token = config.get('setup', 'api_token')

client = OpenAI(base_url=base_url, api_key="not_needed")

bot = telebot.TeleBot(api_token)
bot.set_my_commands(commands=[
    telebot.types.BotCommand("new_context", "New context"),
    telebot.types.BotCommand("reset_history", "Reset history"),
    telebot.types.BotCommand("get_models", "Get models"),
    telebot.types.BotCommand("go_back", "Go back"),
])

CHATTING = "chatting"
NEW_CONTEXT = "new_context"
MAX_MESSAGE_LENGTH = 4096

db = {
    "user": dict()
}

USER = "user"
ASSISTANT = "assistant"
SYSTEM = "system"


class User:
    def __init__(self, user_id):
        self.id = user_id
        self.history = []
        self.state = CHATTING
        self.context = "You are a helpful ai assistant."

    def add_to_history(self, role, content):
        self.history.append({"role": role, "content": content})

    def set_context(self, description):
        self.context = description

    def prepare_prompt(self, prompt):
        messages = self.history.copy()
        messages.insert(0, {"role": SYSTEM, "content": self.context})
        messages.append({"role": USER, "content": prompt})
        return messages


def get_user(user_id) -> User:
    global db
    if user_id not in db['user']:
        db['user'].update({user_id: User(user_id)})
    return db['user'][user_id]


def stream_response(chat_id, response, update_time=1):
    new_message = bot.send_message(chat_id, ">")
    full_response = ""
    complete_response = ""
    last_update_time = time.time()
    for chunk in response:
        chunk_message = chunk.choices[0].delta.content if chunk.choices[0].delta.content is not None else ""
        complete_response += chunk_message
        if len(complete_response) > MAX_MESSAGE_LENGTH:
            separator = complete_response.rfind('\n')
            if separator == -1:
                separator = complete_response.rfind(' ')
            bot.edit_message_text(chat_id=chat_id, text=complete_response[:separator], message_id=new_message.message_id)
            full_response += complete_response[:separator + 1]
            complete_response = complete_response[separator + 1:]
            new_message = bot.send_message(chat_id, ">")
        elif time.time() - last_update_time > update_time:
            bot.edit_message_text(chat_id=chat_id, text=complete_response, message_id=new_message.message_id)
            last_update_time = time.time()
    bot.edit_message_text(chat_id=chat_id, text=complete_response, message_id=new_message.message_id)
    full_response += complete_response
    return full_response


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    print("start")
    user = get_user(message.from_user.id)
    if len(user.history) == 0:
        bot.send_message(message.chat.id, f"[New conversation]")
    else:
        bot.send_message(message.chat.id, f"[Continuing conversation]")


@bot.message_handler(commands=['reset_history'], func=lambda message: get_user(message.from_user.id).state == CHATTING)
def reset_history(message: telebot.types.Message):
    print("reset_h")
    user = get_user(message.from_user.id)
    user.history = []
    bot.send_message(message.chat.id, "[Chat history has been reset]")


@bot.message_handler(commands=['new_context'], func=lambda message: get_user(message.from_user.id).state == CHATTING)
def edit_context(message: telebot.types.Message):
    user = get_user(message.from_user.id)
    user.state = NEW_CONTEXT
    bot.send_message(message.chat.id, f"[Current context:\n{user.context}]\nWrite new context:")


@bot.message_handler(content_types=['text'], func=lambda message: get_user(message.from_user.id).state == NEW_CONTEXT)
def edit_context_2(message: telebot.types.Message):
    print("text")
    user = get_user(message.from_user.id)
    user.state = CHATTING
    user.set_context(message.text)
    bot.send_message(message.chat.id, f"[New context:\n{user.context}]")


@bot.message_handler(commands=['get_models'], func=lambda message: get_user(message.from_user.id).state == CHATTING)
def get_models(message: telebot.types.Message):
    bot.send_message(message.chat.id, f"[Available models:\n{client.models.list()}]")


@bot.message_handler(commands=['go_back'], func=lambda message: get_user(message.from_user.id).state == CHATTING)
def go_back(message: telebot.types.Message):
    user = get_user(message.chat.id)
    user.history = user.history[:-2]
    bot.send_message(message.chat.id, f"[Last exchange erased]")


@bot.message_handler(content_types=['text'], func=lambda message: get_user(message.from_user.id).state == CHATTING)
def chatting(message: telebot.types.Message):
    user = get_user(message.from_user.id)
    response = client.chat.completions.create(
        model="",
        messages=user.prepare_prompt(message.text),
        stream=True
    )
    full_response = stream_response(message.chat.id, response)
    user.add_to_history(USER, message.text)
    user.add_to_history(ASSISTANT, full_response)


bot.infinity_polling()
