import pytest
from markdownviewer.render import markdown_to_html, render_file


def test_markdown_to_html_converts_heading():
    html = markdown_to_html("# Title")
    assert "<h1>Title</h1>" in html


def test_markdown_to_html_wraps_in_style_block():
    html = markdown_to_html("body text")
    assert "<style>" in html
    assert "</style>" in html


def test_markdown_to_html_handles_garbled_input_without_raising():
    html = markdown_to_html("# Unclosed *bold\n\n[bad link](")
    assert isinstance(html, str)


def test_render_file_reads_and_converts(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("# Hello\n\nSome **bold** text.", encoding="utf-8")

    html = render_file(md_file)

    assert "<h1>Hello</h1>" in html
    assert "<strong>bold</strong>" in html


def test_render_file_missing_file_raises(tmp_path):
    missing = tmp_path / "does-not-exist.md"

    with pytest.raises(FileNotFoundError):
        render_file(missing)


def test_render_file_bad_encoding_raises(tmp_path):
    bad_file = tmp_path / "bad-encoding.md"
    bad_file.write_bytes(b"\xff\xfe# not valid utf-8 \xff")

    with pytest.raises(UnicodeDecodeError):
        render_file(bad_file)


def test_render_file_strips_utf8_bom(tmp_path):
    bom_file = tmp_path / "bom.md"
    bom_file.write_bytes(b"\xef\xbb\xbf# Title\n")

    html = render_file(bom_file)

    assert "<h1>Title</h1>" in html


def test_markdown_to_html_escapes_raw_html_instead_of_passing_it_through():
    html = markdown_to_html(
        '<meta http-equiv="refresh" content="0;url=https://example.org/x">'
    )

    assert "<meta" not in html
    assert "&lt;meta" in html
