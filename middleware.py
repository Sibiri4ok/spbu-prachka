from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Any, Dict

class DBMiddleware(BaseMiddleware):
    def __init__(self, db_connection):
        self.db_connection = db_connection

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        data["db"] = self.db_connection
        return await handler(event, data)