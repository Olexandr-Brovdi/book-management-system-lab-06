"""Run seven isolated teaching experiments; expected failures stay outside tests/."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT/'docs/results'


def write(folder: Path, name: str, text: str) -> None:
    (folder/name).write_text(text, encoding='utf-8')


def run(folder: Path, label: str, *arguments: str) -> dict:
    report = folder/(label+'.xml')
    command = [sys.executable, '-m', 'pytest', '-c', str(folder/'pytest.ini'),
               '-v', '--tb=short', '--junitxml='+str(report), *arguments]
    result = subprocess.run(command, cwd=folder, capture_output=True, text=True,
                            encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    (RESULTS/(label+'.txt')).write_text(result.stdout+result.stderr, encoding='utf-8')
    suites = ET.parse(report).getroot()
    cases = suites.findall('.//testcase')
    failures = sum(c.find('failure') is not None or c.find('error') is not None for c in cases)
    return dict(exit_code=result.returncode, tests=len(cases), passed=len(cases)-failures,
                failed=failures)


def main() -> None:
    RESULTS.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='lab06-experiments-') as temporary:
        folder = Path(temporary)
        write(folder,'pytest.ini','[pytest]\naddopts =\nasyncio_default_fixture_loop_scope = function\n')
        write(folder,'coverage.ini','[run]\nbranch = True\n[report]\nfail_under = 0\n')
        write(folder,'subject.py','def average_pages(values):\n    return sum(values) // len(values)\n')
        write(folder,'test_weak.py','from subject import average_pages\n\ndef test_weak():\n    average_pages([100,101,101])\n')
        write(folder,'test_strong.py','import pytest\nfrom subject import average_pages\n\ndef test_strong():\n    assert average_pages([100,101,101]) == pytest.approx(302/3)\n')
        weak = run(folder,'experiment_01_weak','test_weak.py','--cov=subject',
                   '--cov-config='+str(folder/'coverage.ini'),
                   '--cov-report=json:'+str(folder/'weak-coverage.json'))
        strong = run(folder,'experiment_01_strong','test_strong.py')
        weak_coverage = json.loads((folder/'weak-coverage.json').read_text())['totals']
        assert weak['exit_code'] == 0 and strong['exit_code'] == 1
        write(folder,'classification.py','''def classify_pages(pages):
    if pages >= 500:
        return "large"
    if pages >= 100:
        return "medium"
    return "small"
''')
        write(folder,'test_branch.py','''from classification import classify_pages
def test_large():
    assert classify_pages(600) == "large"
def test_medium():
    assert classify_pages(200) == "medium"
def test_small():
    assert classify_pages(50) == "small"
''')
        branches=[]
        for label, select in [('partial','not small'),('complete','large or medium or small')]:
            info = run(folder,'experiment_03_'+label,'test_branch.py','-k',select,
                       '--cov=classification','--cov-branch',
                       '--cov-config='+str(folder/'coverage.ini'),
                       '--cov-report=json:'+str(folder/(label+'.json')))
            totals = json.loads((folder/(label+'.json')).read_text())['totals']
            info.update(branches=totals['num_branches'],covered_branches=totals['covered_branches'],
                        missing_branches=totals['missing_branches'])
            branches.append(info)
        assert branches[0]['missing_branches'] > 0 and branches[1]['missing_branches'] == 0
        write(folder,'test_mock_fake.py','''from unittest.mock import Mock
from book_catalog.models import Book
from book_catalog.protocols import BookRepository
from book_catalog.repositories import InMemoryBookRepository
def test_mock_interaction():
    book = Book("9780000000002","Кобзар","Тарас Шевченко",1840,240)
    repository = Mock(spec=BookRepository)
    repository.all.return_value = (book,)
    assert repository.all() == (book,)
    repository.all.assert_called_once_with()
def test_fake_state():
    book = Book("9780000000002","Кобзар","Тарас Шевченко",1840,240)
    repository = InMemoryBookRepository()
    repository.add(book)
    assert repository.all() == (book,)
''')
        doubles = run(folder,'experiment_04_mock_fake','test_mock_fake.py')
        write(folder,'test_flaky.py','''import random
import pytest
rng = random.Random(17)  # Reproducible replay of a random-dependent bad test.
@pytest.mark.parametrize("attempt",range(20))
def test_random_bad(attempt):
    assert rng.randint(1,2) == 1
''')
        flaky = run(folder,'experiment_05_flaky','test_flaky.py')
        write(folder,'test_deterministic.py','''import random
import pytest
@pytest.mark.parametrize("attempt",range(20))
def test_random_controlled(attempt,monkeypatch):
    monkeypatch.setattr(random,"randint",lambda a,b: 1)
    assert random.randint(1,2) == 1
''')
        fixed = run(folder,'experiment_05_deterministic','test_deterministic.py')
        assert 0 < flaky['failed'] < 20 and fixed['passed'] == 20
        write(folder,'test_isolation.py','''from pathlib import Path
def test_file_is_isolated(tmp_path):
    target = tmp_path/"result.txt"
    assert not target.exists()
    target.write_text("fresh",encoding="utf-8")
    assert target.read_text() == "fresh"
    Path("observed-path.txt").write_text(str(tmp_path),encoding="utf-8")
''')
        before = {p.name:p.read_bytes() for p in (ROOT/'output').glob('*') if p.is_file()}
        isolation=[]
        paths=[]
        for number in range(3):
            isolation.append(run(folder,f'experiment_06_isolation_{number+1}',
                                 'test_isolation.py','--basetemp='+str(folder/f'run-{number+1}')))
            paths.append((folder/'observed-path.txt').read_text(encoding='utf-8'))
        after = {p.name:p.read_bytes() for p in (ROOT/'output').glob('*') if p.is_file()}
        assert len(set(paths)) == 3 and before == after
        failure = run(folder,'experiment_07_failure_path',str(ROOT/'tests/unit/test_services.py'),
                      '-k','report_uses_repository or repository_failure_prevents',
                      '--rootdir='+str(ROOT))
        assert all(x['exit_code'] == 0 for x in [doubles,fixed,failure,*isolation,*branches])
        summary = dict(
            weak_vs_strong=dict(weak=weak,strong=strong),
            coverage_without_assertions=dict(statement_percent=weak_coverage['percent_covered'],
                                               incorrect_result=100,expected_result=302/3),
            branch_coverage=branches,
            mock_vs_fake=doubles,
            flaky=dict(random_replay=flaky,deterministic=fixed,seed=17),
            isolation=dict(runs=isolation,unique_directories=len(set(paths)),repository_output_unchanged=before==after),
            failure_path=failure,
        )
        (RESULTS/'experiments.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        for name in ['subject.py','test_weak.py','test_strong.py','classification.py',
                     'test_branch.py','test_mock_fake.py','test_flaky.py','test_deterministic.py','test_isolation.py']:
            destination=ROOT/'docs/experiment_sources'/name
            destination.parent.mkdir(exist_ok=True)
            destination.write_bytes((folder/name).read_bytes())
        print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
