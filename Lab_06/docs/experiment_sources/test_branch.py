from classification import classify_pages
def test_large():
    assert classify_pages(600) == "large"
def test_medium():
    assert classify_pages(200) == "medium"
def test_small():
    assert classify_pages(50) == "small"
