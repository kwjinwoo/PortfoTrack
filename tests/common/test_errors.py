from portfotrack.common.errors import AppError


def test_app_error_minal_init() -> None:
    e = AppError(code="X", message="m")
    assert e.code == "X"
    assert e.message == "m"
    assert e.details == {}
    assert e.cause is None


def test_app_error_cause_preserved() -> None:
    root = ValueError("root")
    e = AppError(code="X", message="m", cause=root)
    assert e.cause is root


def test_app_error_exception_args_contains_message() -> None:
    e = AppError(code="X", message="m")
    assert e.args == ("m",)


def test_app_error_str_format() -> None:
    e = AppError(code="X", message="m")
    assert str(e) == "[X] m"
