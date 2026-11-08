"""Audit lab identity, autonomous layout and actual pytest/experiment evidence."""
from pathlib import Path
import ast
import json
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]


def validate() -> None:
    if ROOT.name=='Lab_06':
        reports=[ROOT/'report/report.docx']
    else:
        reports=[ROOT/'docs/Lab_06_Report_Variant_2.docx',ROOT/'Lab_06/report/report.docx']
    for report in reports:
        with ZipFile(report) as archive:
            raw=archive.read('word/document.xml')
        assert b'Aspose' not in raw
        tree=ET.fromstring(raw)
        text=' '.join(t.text or '' for t in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')).casefold()
        for required in ['лабораторної роботи №6','варіант №2','бровді олександр',
                         'система обліку книг','pytest','asyncmock','monkeypatch',
                         '97 passed','80.','228/228','44/44','regression']:
            assert required in text,required
        assert set(re.findall(r'варіант\s*№?\s*(\d+)',text))=={'2'}
        assert 'заставний денис' not in text
    assert {p.resolve() for p in ROOT.rglob('*.docx') if '.venv' not in p.parts}=={p.resolve() for p in reports}
    if len(reports)==2:
        assert reports[0].read_bytes()==reports[1].read_bytes()
        for folder in ['src','tests','data','tools']:
            for path in (ROOT/folder).rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts and not any(x.endswith('.egg-info') for x in path.parts):
                    assert path.read_bytes()==(ROOT/'Lab_06'/path.relative_to(ROOT)).read_bytes(),path
    coverage=json.loads((ROOT/'docs/results/coverage.json').read_text())['totals']
    assert coverage['covered_lines']==coverage['num_statements']==228
    assert coverage['covered_branches']==coverage['num_branches']==44
    cases=ET.parse(ROOT/'docs/results/tests.xml').findall('.//testcase')
    assert len(cases)==97
    assert not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
    assert sum('integration' in c.attrib['classname'] for c in cases)==8
    functions=[]
    for path in (ROOT/'tests/unit').glob('test_*.py'):
        functions.extend(n for n in ast.walk(ast.parse(path.read_text(encoding='utf-8')))
                         if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_'))
    assert len(functions)>=15
    evidence=json.loads((ROOT/'docs/results/experiments.json').read_text())
    assert len(evidence)==7
    assert evidence['weak_vs_strong']['strong']['failed']==1
    assert evidence['coverage_without_assertions']['statement_percent']==100
    assert evidence['branch_coverage'][0]['covered_branches']==3
    assert evidence['branch_coverage'][1]['covered_branches']==4
    assert evidence['flaky']['deterministic']['passed']==20
    assert evidence['isolation']['unique_directories']==3
    assert evidence['isolation']['repository_output_unchanged']
    assert len(json.loads((ROOT/'docs/control_answers.json').read_text(encoding='utf-8')))==80
    print('PASS: Lab_06 variant 2; report identity; 97 passed; 100% statements/branches; seven experiments; 80 answers.')


if __name__=='__main__':
    validate()
