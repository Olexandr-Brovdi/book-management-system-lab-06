import random
import pytest
rng = random.Random(17)  # Reproducible replay of a random-dependent bad test.
@pytest.mark.parametrize("attempt",range(20))
def test_random_bad(attempt):
    assert rng.randint(1,2) == 1
