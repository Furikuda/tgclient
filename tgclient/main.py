import json

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Input, RichLog

import client

class TelegramMessage(Message):
    def __init__(self, event):
        self.event = event
        super().__init__()



class PopUp(Screen[str]):

    def __init__(self, question: str, placeholder='') -> None:
        self.question = question
        self.placeholder = placeholder
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label(self.question)
        yield Input(placeholder=self.placeholder)
        yield Button("Send", id="submit", variant="success")

    @on(Input.Submitted)
    def on_input(self) -> None:
        input_text = self.query_one(Input)
        text = input_text.value
        self.dismiss(text)


class Main(App):
    CSS_PATH = "main.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, api_id, api_hash):
        super().__init__()

        self.tgclient = None
        self.api_id = api_id
        self.api_hash = api_hash
        self.processes = []

        self.text_log = None

    def compose(self) -> ComposeResult:
        """Compose our UI."""

        yield Header()
        with VerticalScroll(id="telegram"):
            yield RichLog(id="telegram-client", auto_scroll=True, wrap=True)
        yield Footer()


    @work
    @on(TelegramMessage)
    async def _handle_tg_event(self, message):
#        phone_number = self._ask_question_str('Please enter your phone number')
        event = message.event
        j = json.dumps(event)
        self.add_log_line(f'Received: {j}')
        if event['@type'] == 'updateAuthorizationState':
            auth_state = event['authorization_state']
            if auth_state['@type'] == 'authorizationStateWaitPhoneNumber':
                phone_number = await self.push_screen_wait(PopUp('Phone number'))
                self.tgclient.td_send({'@type': 'setAuthenticationPhoneNumber', 'phone_number': phone_number})
            if auth_state['@type'] == 'authorizationStateWaitEmailAddress':
                email_address = await self.push_screen_wait(PopUp('Email address'))
                self.tgclient.td_send({'@type': 'setAuthenticationEmailAddress', 'email_address': email_address})
            if auth_state['@type'] == 'authorizationStateWaitCode':
                code = await self.push_screen_wait(PopUp('Please enter the authentication code you received: '))
                self.tgclient.td_send({'@type': 'checkAuthenticationCode', 'code': code})
            if auth_state['@type'] == 'authorizationStateWaitEmailCode':
                code = await self.push_screen_wait(PopUp('Please enter the authentication code you received'))
                self.tgclient.td_send(
                        {'@type': 'checkAuthenticationEmailCode',
                         'code': {'@type': 'emailAddressAuthenticationCode', 'code' : code}})
            if auth_state['@type'] == 'authorizationStateWaitRegistration':
                first_name = await self.push_screen_wait(PopUp('Please enter your first name: '))
                last_name = await self.push_screen_wait(PopUp('Please enter your last name: '))
                self.tgclient.td_send({'@type': 'registerUser', 'first_name': first_name, 'last_name': last_name})
            if auth_state['@type'] == 'authorizationStateWaitPassword':
                password = await self.push_screen_wait(PopUp('Please enter your password: '))
                self.tgclient.td_send({'@type': 'checkAuthenticationPassword', 'password': password})
            if auth_state['@type'] == 'authorizationStateWaitTdlibParameters':
                self.tgclient.send_tdlib_parameters()
        else:
            self.tgclient.handle_event(event)

    def add_log_line(self, line):
        self.text_log.write(line)


    @work(thread=True)
    def run_tgclient(self):
        self.tgclient = client.TelegramClient(self.api_id, self.api_hash)
        while True:
            event = self.tgclient.td_receive()
            if event:
                self.post_message(TelegramMessage(event))

    @work
    async def on_mount(self):
        self.text_log = self.query_one(RichLog)
        self.run_tgclient()


if __name__ == "__main__":
    with open("config.json", 'r') as f:
        conf = json.load(f)

        m = Main(conf['api_id'], conf['api_hash'])
        m.run()
