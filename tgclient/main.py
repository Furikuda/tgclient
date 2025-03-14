from multiprocessing import Process, Queue

import json

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Label, Input, RichLog

import client

class PopUp(Screen[str]):

    def __init__(self, question: str, placeholder='') -> None:
        self.question = question
        self.placeholder = placeholder
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label(self.question)
        yield Input(placeholder=self.placeholder)
        yield Button("Yes", id="yes", variant="success")

    @on(Button.Pressed, "#yes")
    def handle_yes(self, event):
        self.dismiss("coin")

#    @on(Input.Submitted)
#    def on_input(self) -> None:
#        input_text = self.query_one(Input)
#        text = input_text.value
#        self.dismiss(text)


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

    def compose(self) -> ComposeResult:
        """Compose our UI."""

        yield Header()
        with VerticalScroll(id="telegram"):
            yield RichLog(id="telegram-client", auto_scroll=True)
        yield Footer()

    async def _ask_question_str(self, s):
        return await self.push_screen_wait(PopUp(s))

#    @on(LogMessage)
#    def handle_event(self, event: LogMessage):
#        phone_number =  self._ask_question_str('Please enter your phone number')
#        text_log = self.query_one(RichLog)
#        j = json.dumps(event.event).encode('utf-8')
#        text_log.write(j)

    async def _handle_tg_event(self, event):


        phone_number = await self._ask_question_str('Please enter your phone number')
#        text_log = self.query_one(RichLog)
#        j = json.dumps(event).encode('utf-8')
#        text_log.write(j)
#        if event['@type'] == 'updateAuthorizationState':
#            auth_state = event['authorization_state']
#            if auth_state['@type'] == 'authorizationStateWaitPhoneNumber':
#                text_log.write('We need to ask for phone number')
#                phone_number =  self._ask_question_str('Please enter your phone number')
#                self.tgclient.td_send({'@type': 'setAuthenticationPhoneNumber', 'phone_number': phone_number})
#        else:
#            self.tgclient.handle_event(event)


    def _background_tgworker_start(self):
        self.tgclient.main_loop(handle_event=self._handle_tg_event)

    def on_mount(self):
        self.tgclient = client.TelegramClient(self.api_id, self.api_hash)

        tg_events_queue = Queue()

        tgworker = Process(target=self.tgclient.main_loop, args=(tg_events_queue))
        tgworker.start()
        self.processes.append(tgworker)



if __name__ == "__main__":
    with open("config.json", 'r') as f:
        conf = json.load(f)

        m = Main(conf['api_id'], conf['api_hash'])
        m.run()
