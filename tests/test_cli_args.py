from markdownviewer.app import paths_from_argv


def test_existing_file_is_resolved(tmp_path):
    md = tmp_path / "a.md"
    md.write_text("# hi", encoding="utf-8")

    found, missing = paths_from_argv([str(md)])

    assert found == [md.resolve()]
    assert missing == []


def test_missing_file_is_reported(tmp_path):
    ghost = str(tmp_path / "nope.md")

    found, missing = paths_from_argv([ghost])

    assert found == []
    assert missing == [ghost]


def test_no_args_opens_nothing():
    assert paths_from_argv([]) == ([], [])
