import sqlite3
import json
from constants import *


class TgBotDatabase:
    def __init__(self, database_file):
        self.filename = database_file
        self.create_chats_table()

    def connect(self):
        return sqlite3.connect(self.filename)

    def create_chats_table(self):
        with self.connect() as connection:
            connection.execute(CREATE_CHATS_TABLE)

    def get_chats(self):
        with self.connect() as connection:
            chats = connection.execute(GET_CHATS).fetchall()
        return [(chat["id"], json.loads(chat["messages"])) for chat in chats]

    def new_chat(self, chat_id: int):
        with self.connect() as connection:
            connection.execute(NEW_CHAT, (chat_id,))
        return {"id": chat_id, "messages": []}

    def update_chat(self, chat_id: int, messages: List):
        with self.connect() as connection:
            connection.execute(UPDATE_CHAT, (json.dumps(messages),))


CHATS_TABLE = "chats"

GET_CHATS = f"""
SELECT * FROM {CHATS_TABLE}
"""

CREATE_CHATS_TABLE = f"""
CREATE TABLE IF NOT EXISTS {CHATS_TABLE} (
    id integer PRIMARY KEY,
    messages text DEFAULT "[]"
)
"""

NEW_CHAT = f"""
INSERT OR IGNORE INTO {CHATS_TABLE} (id) VALUES (?)
"""

UPDATE_CHAT = f"""
UPDATE {CHATS_TABLE} SET messages = ? WHERE id = ?
"""

GET_CHAT = f"""
SELECT * FROM {CHATS_TABLE} WHERE id = ?
"""
