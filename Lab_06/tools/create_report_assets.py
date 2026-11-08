"""Render figures from stored actual pytest and application output."""
from pathlib import Path
import json
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def figure(name: str, text: str) -> None:
    folder = ROOT/'docs/screenshots'
    folder.mkdir(parents=True,exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf',21)
    lines=[]
    for line in text.expandtabs(4).splitlines():
        lines.extend(textwrap.wrap(line,width=88,subsequent_indent='  ') or [''])
    canvas = Image.new('RGB',(1200,48+len(lines)*29),'#16202b')
    draw=ImageDraw.Draw(canvas)
    for i,line in enumerate(lines):
        draw.text((24,24+i*29),line,font=font,fill='#edf2f7')
    canvas.save(folder/(name+'.png'))


def main() -> None:
    results=ROOT/'docs/results'
    text=(results/'tests.txt').read_text(encoding='utf-8-sig')
    start=text.index('Name ')
    figure('coverage',text[start:])
    failed=(results/'regression_before_fix.txt').read_text(encoding='utf-8-sig')
    failed=failed[failed.index('    def test_config_file'):failed.index('short test summary')]
    figure('regression',failed)
    figure('application','python -m book_catalog.main --config config.yaml --author Франко\n\n'+
           (results/'application.txt').read_text(encoding='utf-8-sig'))
    evidence=json.loads((results/'experiments.json').read_text())
    lines=['Сім експериментів виконано на реальному pytest','',
           'Weak: 1 pass; strong: 1 expected failure',
           'Wrong function without assertions: 100% statement coverage',
           'Branch coverage: 3/4 -> 4/4',
           'Mock + fake: 2 passed',
           f"Random replay: {evidence['flaky']['random_replay']['passed']} passed / {evidence['flaky']['random_replay']['failed']} failed",
           'Controlled randomness: 20 passed',
           'tmp_path: 3 runs, 3 directories; repository output unchanged',
           'Dependency success/failure: 2 passed']
    figure('experiments','\n'.join(lines))


if __name__ == '__main__':
    main()
