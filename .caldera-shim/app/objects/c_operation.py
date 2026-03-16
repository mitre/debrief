"""Stub for Caldera Operation."""
from datetime import datetime

class Operation:
    def __init__(self, name='', agents=None, adversary=None, **kwargs):
        self.name = name
        self.agents = agents or []
        self.adversary = adversary
        self.chain = []
        self.id = kwargs.get('id', name)
        self.state = 'finished'
        self.finish = None
        self.created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.source = None
        self.planner = None
        self.objective = None
        self.display = {'name': name}

    def set_start_details(self):
        pass
