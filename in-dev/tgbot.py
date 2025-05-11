from typing import List
import telebot
from database import TgBotDatabase


class TgChat:
    def __init__(self, bot: telebot.TeleBot, chat_id: int, messages: List[telebot.types.Message] = None):
        self.bot = bot
        self.id = chat_id
        self.messages = messages if messages is not None else []

    def find_index(self, message_id: int) -> int | None:
        for i in range(len(self.messages)):
            if self.messages[i].id == message_id:
                return i
        return None

    def send(self, text: str) -> telebot.types.Message:
        new_message = self.bot.send_message(self.id, text)
        self.messages.append(new_message)
        return new_message

    def delete(self, message_ids: List[int]):
        self.bot.delete_messages(self.id, message_ids)
        self.messages = list(filter(lambda msg: msg.id not in message_ids, self.messages))

    def edit_text(self, message_id: int, text: str) -> telebot.types.Message:
        edited_message = self.bot.edit_message_text(text, self.id, message_id)
        self.messages[self.find_index(message_id)] = edited_message
        return edited_message

    def empty(self):
        return len(self.messages) == 0


class TgBot(telebot.TeleBot):
    def __init__(self, token: str, database_file: str = None, **kwargs):
        super().__init__(token, **kwargs)  # TODO: error checks
        if database_file is not None:
            self.database = TgBotDatabase(database_file)
            self.chats = list(map(TgChat, self.database.get_chats()))

    def get_chat(self, chat_id) -> TgChat:
        if chat_id not in self.chats:
            self.chats[chat_id] = TgChat(self, chat_id)
            self.database.new_chat(chat_id)
        return self.chats[chat_id]
