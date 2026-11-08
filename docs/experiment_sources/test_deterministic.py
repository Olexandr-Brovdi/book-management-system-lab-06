import random
import pytest
@pytest.mark.parametrize("attempt",range(20))
def test_random_controlled(attempt,monkeypatch):
    monkeypatch.setattr(random,"randint",lambda a,b: 1)
    assert random.randint(1,2) == 1
