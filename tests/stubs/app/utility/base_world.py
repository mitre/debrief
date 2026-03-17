"""Stub for Caldera BaseWorld."""
from enum import Enum


class BaseWorld:
    class Access(Enum):
        RED = 'red'
        BLUE = 'blue'
        APP = 'app'

    @staticmethod
    def get_config(prop=None, name=None):
        return None

    @staticmethod
    def apply_config(name, config):
        pass

    @staticmethod
    def strip_yml(path):
        return [{}]
