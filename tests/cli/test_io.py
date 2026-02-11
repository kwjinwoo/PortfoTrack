from portfotrack.cli.io import print_help


def test_print_help_includes_snapshot_save_and_load(capsys) -> None:
    print_help()

    out = capsys.readouterr().out
    assert "save-snapshot" in out
    assert "load-snapshot" in out
