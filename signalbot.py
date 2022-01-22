#!/usr/bin/python3.9
# Copyright (c) 2021 MobileCoin Inc.
# Copyright (c) 2021 The Forest Team

from forest.core import Bot, Message, Response, run_bot
from berduck.core import respond

class DuckBot(Bot):
    async def handle_message(self, message: Message) -> Response:
        """Method dispatch to do_x commands and goodies.
        Overwrite this to add your own non-command logic,
        but call super().handle_message(message) at the end"""
        if message.arg0:
            if hasattr(self, "do_" + message.arg0):
                return await getattr(self, "do_" + message.arg0)(message)
            suggest_help = " Try /help." if hasattr(self, "do_help") else ""
        if message.full_text == "TERMINATE":
            return "signal session reset"
        if message.full_text:
            return await self.default(message)

    async def do_duck(self, message: Message) -> str:
        return respond(message.full_text)

    async def default(self, message: Message) -> Response:
        # if it messages an echoserver, don't get in a loop (or groups)
        if message.full_text and not message.group:
            return await self.do_duck(message)
        return None


if __name__ == "__main__":
    run_bot(DuckBot)
