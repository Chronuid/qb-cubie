"""Reviewed reference templates; no claim that a v6 generator exists yet.

The renderer only substitutes the condition's assertion syntax. Targets and
observation adapters below call the public production fixture in fixtures/v6.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Form:
    id: str
    requirement: str
    public_reason: str
    setup: str
    target: str
    args: str
    kwargs: str
    expected: str
    broken_from: str
    broken_to: str
    exception: bool = False


FORMS = (
    Form("F01", "REQ-F01", "double(1)=2 and double(2)=4; the pairs must not be swapped.",
         '@pytest.mark.parametrize("value, expected", [(1, 2), (2, 4)])\n'
         'def test_case(value, expected):\n',
         "app.double", "(value,)", "{}", "expected", "return value * 2", "return 6 - value * 2"),
    Form("F02", "REQ-F02", "The provided keyword prefix must be preserved, including Unicode.",
         'def test_case():\n', "app.greet", '("Ada",)', '{"prefix": "Grüß dich, "}',
         '"Grüß dich, Ada"', "return prefix + name", 'return "Hello " + name'),
    Form("F03", "REQ-F03", "A zero denominator raises ValueError with the documented message.",
         'def test_case():\n', "app.divide", "(1, 0)", "{}", 'ValueError',
         'raise ValueError("denominator must be nonzero")', "return 0", exception=True),
    Form("F04", "REQ-F04", "Adding 3 to a fixture Counter(2) returns and stores 5.",
         '@pytest.fixture\ndef counter():\n    return app.Counter(2)\n\n'
         'def test_case(counter):\n'
         '    def observe(amount):\n'
         '        returned = counter.add(amount)\n'
         '        return returned, counter.total\n',
         "observe", "(3,)", "{}", "(5, 5)", "self.total += amount", "self.total = amount"),
    Form("F05", "REQ-F05", "The WSGI application returns 200 OK, JSON content type and the exact body.",
         'def test_case():\n'
         '    def observe():\n'
         '        headers = []\n'
         '        body = app.application({"PATH_INFO": "/health", "REQUEST_METHOD": "GET"},\n'
         '                               lambda status, fields: headers.append((status, fields)))\n'
         '        return headers[0][0], dict(headers[0][1])["Content-Type"], b"".join(body)\n',
         "observe", "()", "{}", '("200 OK", "application/json", b\'{"status":"ok"}\')',
         'return [b\'{"status":"ok"}\']', 'return [b"{}"]'),
    Form("F06", "REQ-F06", "Terminal output includes the exact READY line and one newline.",
         'def test_case():\n'
         '    def observe():\n'
         '        console = io.StringIO()\n'
         '        app.render_status(console)\n'
         '        return console.getvalue()\n',
         "observe", "()", "{}", '"READY\\n"', 'console.write("READY\\n")', 'console.write("WAIT\\n")'),
    Form("F07", "REQ-F07", "The report file preserves Unicode and the final newline; tmp_path cleans up.",
         'def test_case(tmp_path):\n'
         '    def observe(text):\n'
         '        path = tmp_path / "report.txt"\n'
         '        app.write_report(path, text)\n'
         '        return path.is_file(), path.read_text(encoding="utf-8")\n',
         "observe", '("Grüße\\n",)', "{}", '(True, "Grüße\\n")',
         'path.write_text(text, encoding="utf-8")', 'path.write_text(text.strip(), encoding="utf-8")'),
)


def render(form, mode):
    header = "import io\nimport pytest\nimport app\n"
    if mode == "cubie":
        header += "from qb_cubie import EBT, ExceptionExpectation, WorldState\n"
        post = ('raises=ExceptionExpectation(ValueError, match=r"^denominator must be nonzero$")'
                if form.exception else f"returns={form.expected}")
        check = (
            f"    result = EBT(target={form.target}, "
            f"pre=WorldState(args={form.args}, kwargs={form.kwargs}), "
            f"post=WorldState({post}), reporter=None).run()\n"
            "    assert result.evaluation is True\n"
        )
    elif mode == "pytest":
        call = f"{form.target}(*{form.args}, **{form.kwargs})"
        check = ('    with pytest.raises(ValueError, match=r"^denominator must be nonzero$"):\n'
                 f"        {call}\n" if form.exception else f"    assert {call} == {form.expected}\n")
    else:
        raise ValueError(f"Unsupported template condition: {mode}")
    return header + "\n\n" + form.setup + check
