import ctypes
from ctypes.util import find_library
import json
import os

class TelegramError(Exception):
    pass

class TelegramClient:
    def __init__(self, api_id, api_hash, tdlib_database_directory=None):
        self.log_file = open("/tmp/tdlog.json", "ab+")

        self.tdlib_database_directory = tdlib_database_directory
        if not tdlib_database_directory:
            self.tdlib_database_directory = 'tdlib'

        self.api_id = api_id
        self.api_hash = api_hash

        self._init_tdlib()

        self._init_client()
        self.log_str('TG Client init')

    def _init_client(self):
        self.td_execute({'@type': 'setLogVerbosityLevel', 'new_verbosity_level': 1, '@extra': 1.01234})
        # create client
        self.client_id = self._td_create_client_id()
        # another test for TDLib execute method
#        print(str(self.td_execute({'@type': 'getTextEntities', 'text': '@telegram /test_command https://telegram.org telegram.me', '@extra': ['5', 7.0, 'a']})).encode('utf-8'))

        # start the client by sending a request to it
        self.td_send({'@type': 'getOption', 'name': 'version', '@extra': 1.01234})


    # simple wrappers for client usage
    def td_send(self, query):
        query = json.dumps(query).encode('utf-8')
        self.log_str(f'Executed {query}')
        self._td_send(self.client_id, query)

    def td_receive(self):
        result = self._td_receive(1.0)
        if result:
            result = json.loads(result.decode('utf-8'))
        return result

    def td_execute(self, query):
        query = json.dumps(query).encode('utf-8')
        self.log_str(f'Executed {query}')
        result = self._td_execute(query)
        if result:
            result = json.loads(result.decode('utf-8'))
        return result

    def _init_tdlib(self):
        # load shared library
        tdjson_path = find_library('tdjson')
        if tdjson_path is None:
            if os.name == 'nt':
                tdjson_path = os.path.join(os.path.dirname(__file__), 'tdjson.dll')
            else:
                raise TelegramError("Can't find 'tdjson' library. Run td_install.sh")
        tdjson = ctypes.CDLL(tdjson_path)

        # load TDLib functions from shared library
        self._td_create_client_id = tdjson.td_create_client_id
        self._td_create_client_id.restype = ctypes.c_int
        self._td_create_client_id.argtypes = []

        self._td_receive = tdjson.td_receive
        self._td_receive.restype = ctypes.c_char_p
        self._td_receive.argtypes = [ctypes.c_double]

        self._td_send = tdjson.td_send
        self._td_send.restype = None
        self._td_send.argtypes = [ctypes.c_int, ctypes.c_char_p]

        self._td_execute = tdjson.td_execute
        self._td_execute.restype = ctypes.c_char_p
        self._td_execute.argtypes = [ctypes.c_char_p]

        self.log_message_callback_type = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)

        _td_set_log_message_callback = tdjson.td_set_log_message_callback
        _td_set_log_message_callback.restype = None
        _td_set_log_message_callback.argtypes = [ctypes.c_int, self.log_message_callback_type]

#        _td_set_log_message_callback(2, on_log_message_callback)

    def log_str(self, s):
        self.log_bytes(s.encode('utf-8'))


    def log_bytes(self, b):
        self.log_file.write(b+b"\n")
        self.log_file.flush()

    def log(self, event):
        j = json.dumps(event)
        self.log_str(j)

    def send_tdlib_parameters(self):
        self.td_send({'@type': 'setTdlibParameters',
                 'database_directory': self.tdlib_database_directory,
                 'use_message_database': True,
                 'use_secret_chats': True,
                 'api_id': self.api_id,
                 'api_hash': self.api_hash,
                 'system_language_code': 'en',
                 'device_model': 'Desktop',
                 'application_version': '1.0'})


    def handle_event(self, event):
        if event['@type'] == 'updateUser':
            uid = event['user']['id']
            self.td_send({'@type': 'getGroupsInCommon', 'user_id': uid, 'offset': 0, 'limit': 20, '@extra': ['pouet', uid, 1.01234]})
        if event['@type'] == 'updateAuthorizationState':
            auth_state = event['authorization_state']

            # if client is closed, we need to destroy it and create new client
            if auth_state['@type'] == 'authorizationStateClosed':
                return

            # set TDLib parameters
            # you MUST obtain your own api_id and api_hash at https://my.telegram.org
            # and use them in the setTdlibParameters call
            if auth_state['@type'] == 'authorizationStateWaitTdlibParameters':
                self.td_send({'@type': 'setTdlibParameters',
                         'database_directory': self.tdlib_database_directory,
                         'use_message_database': True,
                         'use_secret_chats': True,
                         'api_id': self.api_id,
                         'api_hash': self.api_hash,
                         'system_language_code': 'en',
                         'device_model': 'Desktop',
                         'application_version': '1.0'})

            # enter phone number to log in
            if auth_state['@type'] == 'authorizationStateWaitPhoneNumber':
                phone_number = input('Please enter your phone number: ')
                self.td_send({'@type': 'setAuthenticationPhoneNumber', 'phone_number': phone_number})

            # enter email address to log in
            if auth_state['@type'] == 'authorizationStateWaitEmailAddress':
                email_address = input('Please enter your email address: ')
                self.td_send({'@type': 'setAuthenticationEmailAddress', 'email_address': email_address})

            # wait for email authorization code
            if auth_state['@type'] == 'authorizationStateWaitEmailCode':
                code = input('Please enter the email authentication code you received: ')
                self.td_send({'@type': 'checkAuthenticationEmailCode',
                         'code': {'@type': 'emailAddressAuthenticationCode', 'code' : code}})

            # wait for authorization code
            if auth_state['@type'] == 'authorizationStateWaitCode':
                code = input('Please enter the authentication code you received: ')
                self.td_send({'@type': 'checkAuthenticationCode', 'code': code})

            # wait for first and last name for new users
            if auth_state['@type'] == 'authorizationStateWaitRegistration':
                first_name = input('Please enter your first name: ')
                last_name = input('Please enter your last name: ')
                self.td_send({'@type': 'registerUser', 'first_name': first_name, 'last_name': last_name})

            # wait for password if present
            if auth_state['@type'] == 'authorizationStateWaitPassword':
                password = input('Please enter your password: ')
                self.td_send({'@type': 'checkAuthenticationPassword', 'password': password})

#        # initialize TDLib log with desired parameters
#        @self.log_message_callback_type
#        def on_log_message_callback(_, verbosity_level, message):
#            if verbosity_level == 0:
#                sys.exit(f'TDLib fatal error: {message}')

    # main events cycle
    def main_loop(self, handle_event=None):
        if not handle_event:
            handle_event = self.handle_event
        while True:
            event = self.td_receive()
            if event:
                self.log(event)
                handle_event(event)

if __name__ == "__main__":
    with open("config.json", 'r') as f:
        conf = json.load(f)
        t = TelegramClient(conf['api_id'], conf['api_hash'])
        t.main_loop()
