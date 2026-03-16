"""Stub for Caldera auth_svc."""

def for_all_public_methods(decorator):
    def wrapper(cls):
        return cls
    return wrapper

def check_authorization(func):
    return func
