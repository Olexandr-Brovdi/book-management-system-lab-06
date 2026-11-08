from pathlib import Path
def test_file_is_isolated(tmp_path):
    target = tmp_path/"result.txt"
    assert not target.exists()
    target.write_text("fresh",encoding="utf-8")
    assert target.read_text() == "fresh"
    Path("observed-path.txt").write_text(str(tmp_path),encoding="utf-8")
