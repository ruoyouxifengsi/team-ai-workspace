import pytest


def test_sanitize_removes_path_traversal():
    from app.files.storage import sanitize_filename
    assert sanitize_filename("../etc/passwd") == "etc_passwd"
    assert sanitize_filename("a/b/c.txt") == "a_b_c.txt"


def test_sanitize_rejects_empty():
    from app.files.storage import sanitize_filename
    with pytest.raises(ValueError):
        sanitize_filename("")
    with pytest.raises(ValueError):
        sanitize_filename("   ")


def test_sanitize_strips_null_byte_and_long_name():
    from app.files.storage import sanitize_filename
    assert "\x00" not in sanitize_filename("a\x00b.txt")
    name = sanitize_filename("x" * 500 + ".txt")
    assert len(name) <= 255


def test_user_dir_returns_under_data_dir(tmp_path):
    from app.files.storage import user_dir
    p = user_dir(str(tmp_path), user_id=7)
    assert p.exists()
    assert p.is_dir()
    assert str(p).startswith(str(tmp_path))
