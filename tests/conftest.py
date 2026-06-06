from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_rss_setup():
    with patch("src.main.setup_card"):
        with patch("src.main.scheduler"):
            yield
