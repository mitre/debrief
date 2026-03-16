"""Stub for Caldera Agent."""
from datetime import datetime

class Agent:
    def __init__(self, sleep_min=30, sleep_max=60, watchdog=0, platform='', host='',
                 username='', architecture='', group='', location='', pid=0, ppid=0,
                 executors=None, privilege='', exe_name='', contact='', paw='', **kwargs):
        self.sleep_min = sleep_min
        self.sleep_max = sleep_max
        self.watchdog = watchdog
        self.platform = platform
        self.host = host
        self.username = username
        self.architecture = architecture
        self.group = group
        self.location = location
        self.pid = pid
        self.ppid = ppid
        self.executors = executors or []
        self.privilege = privilege
        self.exe_name = exe_name
        self.contact = contact
        self.paw = paw
        self.unique = paw
        self.display_name = paw
        self.created = datetime.now()
        self.origin_link_id = None
