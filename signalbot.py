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
        if message.command:
            if hasattr(self, "do_" + message.command):
                return await getattr(self, "do_" + message.command)(message)
            suggest_help = " Try /help." if hasattr(self, "do_help") else ""
            # return f"Sorry! Command {message.command} not recognized!" + suggest_help
        if message.text == "TERMINATE":
            return "signal session reset"
        return await self.default(message)

    async def do_duck(self, message: Message) -> str:
        return respond(message.text)

    async def default(self, message: Message) -> Response:
        # if it messages an echoserver, don't get in a loop (or groups)
        if message.text and not message.group:
            return await self.do_duck(message)
        return None
        

if __name__ == "__main__":
    run_bot(DuckBot)
