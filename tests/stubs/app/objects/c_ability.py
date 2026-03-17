"""Stub for Caldera Ability."""

class Ability:
    def __init__(self, ability_id='', tactic='', technique_id='', technique_name='',
                 name='', description='', executors=None, **kwargs):
        self.ability_id = ability_id
        self.tactic = tactic
        self.technique_id = technique_id
        self.technique_name = technique_name
        self.name = name
        self.description = description
        self.executors = executors or []
