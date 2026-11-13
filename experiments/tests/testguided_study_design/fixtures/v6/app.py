"""Small public production fixture for qualifying v6 test templates."""


def double(value):
    return value * 2


def greet(name, *, prefix):
    return prefix + name


def divide(numerator, denominator):
    if denominator == 0:
        raise ValueError("denominator must be nonzero")
    return numerator / denominator


class Counter:
    def __init__(self, initial):
        self.total = initial

    def add(self, amount):
        self.total += amount
        return self.total


def application(environ, start_response):
    start_response("200 OK", [("Content-Type", "application/json")])
    return [b'{"status":"ok"}']


def render_status(console):
    console.write("READY\n")


def write_report(path, text):
    path.write_text(text, encoding="utf-8")
