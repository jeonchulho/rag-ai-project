import smtplib
import pytest

class MockSMTP:
    def __init__(self, *args, **kwargs):
        pass
    def starttls(self): pass
    def login(self, user, password): pass
    def send_message(self, msg): print('Mock Email sent:', msg['To'])
    def quit(self): pass
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): pass

@pytest.fixture(autouse=True)
def patch_smtp(monkeypatch):
    monkeypatch.setattr(smtplib, 'SMTP', MockSMTP)
