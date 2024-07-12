from knarkscan.cons import DEFAULT_CONFIG, DEFAULT_CONFIG_FILE, DEFAULT_LOG_LEVEL


def test_constants():
    assert isinstance(DEFAULT_CONFIG_FILE, str)
    assert isinstance(DEFAULT_LOG_LEVEL, str)
    assert isinstance(DEFAULT_CONFIG, dict)
