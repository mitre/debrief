"""Stub for Caldera Link."""
import base64
from datetime import datetime


class Link:
    def __init__(self, command='', plaintext_command='', paw='', ability=None,
                 executor=None, **kwargs):
        self.command = command
        self.plaintext_command = plaintext_command
        self.paw = paw
        self.ability = ability
        self.executor = executor
        self.status = kwargs.get('status', -3)
        self.host = kwargs.get('host', '')
        self.pid = 0
        self.decide = kwargs.get('decide', datetime.now())
        self.collect = kwargs.get('collect', None)
        self.finish = kwargs.get('finish', '')
        self.unique = kwargs.get('unique', str(id(self)))
        self.id = self.unique
        self.cleanup = kwargs.get('cleanup', 0)
        self.facts = kwargs.get('facts', [])
        self.created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def decode_bytes(encoded_cmd):
        try:
            return base64.b64decode(encoded_cmd).decode('utf-8')
        except Exception:
            return str(encoded_cmd)
