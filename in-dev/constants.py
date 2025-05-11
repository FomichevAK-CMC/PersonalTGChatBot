from typing import Union, List, Dict, Tuple

type History = Union[Tuple[Dict], List[Dict]]

CHATTING = "chatting"
NEW_CONTEXT = "new_context"
MAX_MESSAGE_LENGTH = 4096

USER = "user"
ASSISTANT = "assistant"
SYSTEM = "system"

DEFAULT_CONTEXT = "You are a helpful ai assistant."
