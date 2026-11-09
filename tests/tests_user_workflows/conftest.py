"""Only public Cubie APIs are exercised; pytest supplies the outer verdict."""

import pytest


@pytest.fixture(params=["pytest", "silent"])
def check_case(request):
    """Check both user-facing failure and the explicit, unnegated run result."""
    def check(case, *, accepted):
        message = ""
        if request.param == "silent":
            case.reporter = None
            result = case.run()
        elif accepted:
            result = case.run()
        else:
            with pytest.raises(AssertionError, match="EBT-Assert failed") as error:
                case.run()
            message = str(error.value)
            result = case.run_trace
        assert result is not None
        assert result.evaluation is accepted
        assert result.traces, "A verdict without observed execution is not evidence"
        return result, message

    return check
