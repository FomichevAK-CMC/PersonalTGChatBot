from constants import *
from database import BotDatabase
import telebot
import time


class LLMMessagePart:
    def __init__(self, tg_message_id, text: str):
        self.id = tg_message_id
        self.text = text


class LLMMessage:
    def __init__(self, role: str, parts: List[LLMMessagePart]):
        self.parts = parts
        self.role = role

    def full(self):
        return {"role": self.role, "content": ''.join([part.text for part in self.parts])}

    def add_message(self, message_id, text):
        self.parts.append(LLMMessagePart(message_id, text))



class LLMChat:
    def __init__(self, bot, chat_id: int, context: str = "", history: History = None):
        self.bot = bot
        self.id = chat_id
        self.history = list(history) if history is not None else []
        self.state = CHATTING
        self.context = context

    def add_to_history(self, message_id: int, role: str, content: str):
        self.history.append({"message_id": message_id, "content": {"role": role, "content": content}})
        self.bot.database.update_chat_history(self.id, self.history)

    def set_history(self, new_history):
        self.history = new_history
        self.bot.database.update_chat_history(self.id, self.history)

    def set_context(self, description):
        self.context = description
        self.bot.database.update_chat_context(self.id, self.context)

    def prepare_prompt(self, prompt):
        messages = [m["content"] for m in self.history.copy()]
        messages.insert(0, {"role": SYSTEM, "content": self.context})
        messages.append({"role": USER, "content": prompt})
        return messages

    def send_message(self, text):
        return self.bot.send_message(self.id, text)

    def edit_message(self, message_id, text):
        self.bot.edit_message_text(text, self.id, message_id)

    def stream_response(self, response, update_time=1):
        new_message = self.send_message(">")
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
                self.edit_message(new_message.message_id, complete_response[:separator])
                full_response += complete_response[:separator + 1]
                complete_response = complete_response[separator + 1:]
                new_message = self.send_message(">")
            elif time.time() - last_update_time > update_time:
                self.edit_message(new_message.message_id, complete_response)
                last_update_time = time.time()
        self.edit_message(new_message.message_id, complete_response)
        full_response += complete_response
        return full_response


class LLMBot(telebot.TeleBot):
    def __init__(self, token: str, database_file: str):
        super().__init__(token)  # TODO: error checks
        self.database = BotDatabase(database_file)
        self.chats = dict()

    def get_chat(self, chat_id) -> LLMChat:
        if chat_id not in self.chats:
            chat = self.database.get_or_create_chat(chat_id, DEFAULT_CONTEXT)
            self.chats[chat_id] = LLMChat(self, chat_id, chat["context"], chat["history"])
        return self.chats[chat_id]



