import pytest
from subject import average_pages

def test_strong():
    assert average_pages([100,101,101]) == pytest.approx(302/3)
