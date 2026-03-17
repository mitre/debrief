"""Stub for Caldera Adversary."""

class Adversary:
    def __init__(self, adversary_id='', name='', description='', atomic_ordering=None, **kwargs):
        self.adversary_id = adversary_id
        self.name = name
        self.description = description
        self.atomic_ordering = atomic_ordering or {}
