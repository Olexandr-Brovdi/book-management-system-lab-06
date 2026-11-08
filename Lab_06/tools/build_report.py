"""Build both identical Lab_06 reports from actual code, logs and coverage."""
from pathlib import Path
import ast
import json
import re
import shutil
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]


def build() -> None:
    doc=Document()
    section=doc.sections[0]
    section.page_width,section.page_height=Cm(21),Cm(29.7)
    section.top_margin=section.bottom_margin=Cm(2)
    section.left_margin,section.right_margin=Cm(2.5),Cm(1.5)
    for name in ['Normal','Title','Heading 1','Heading 2']:
        style=doc.styles[name]
        style.font.name='Times New Roman'
        style.font.size=Pt(12 if name=='Normal' else 14)
        style.font.color.rgb=RGBColor(0,0,0)
    for border in doc.styles.element.xpath('.//w:pBdr'):
        border.getparent().remove(border)
    normal=doc.styles['Normal'].paragraph_format
    normal.line_spacing=1.05
    normal.space_after=Pt(5)

    def p(text):
        return doc.add_paragraph(text)
    def h(text):
        doc.add_heading(text,level=1)
    def page(title):
        doc.add_page_break()
        h(title)
    def code(text,size=8.5):
        para=p('')
        para.paragraph_format.line_spacing=1
        run=para.add_run(text.strip())
        run.font.name,run.font.size='Consolas',Pt(size)
    def read(path):
        return (ROOT/path).read_text(encoding='utf-8-sig')
    def function(path,name):
        text=read(path)
        for item in ast.walk(ast.parse(text)):
            if isinstance(item,(ast.FunctionDef,ast.AsyncFunctionDef)) and item.name==name:
                start=min([item.lineno,*[d.lineno for d in item.decorator_list]])
                return '\n'.join(text.splitlines()[start-1:item.end_lineno])
        raise ValueError(name)
    def picture(name,caption):
        doc.add_picture(str(ROOT/'docs/screenshots'/(name+'.png')),width=Cm(16.6))
        p(caption)
    def table(headers,rows,widths=None):
        t=doc.add_table(rows=1,cols=len(headers))
        t.autofit=False
        for i,value in enumerate(headers):
            t.rows[0].cells[i].text=str(value)
        for row in rows:
            for cell,value in zip(t.add_row().cells,row):
                cell.text=str(value)
        for rownum,row in enumerate(t.rows):
            for i,cell in enumerate(row.cells):
                if widths:
                    cell.width=Cm(widths[i])
                properties=cell._tc.get_or_add_tcPr()
                borders=OxmlElement('w:tcBorders')
                for edge in ['top','left','bottom','right']:
                    border=OxmlElement('w:'+edge)
                    for key,value in [('val','single'),('sz','4'),('color','D9D9D9')]:
                        border.set(qn('w:'+key),value)
                    borders.append(border)
                properties.append(borders)
                margins=OxmlElement('w:tcMar')
                for edge in ['top','left','bottom','right']:
                    margin=OxmlElement('w:'+edge)
                    margin.set(qn('w:w'),'75')
                    margin.set(qn('w:type'),'dxa')
                    margins.append(margin)
                properties.append(margins)
                if rownum==0:
                    shading=OxmlElement('w:shd')
                    shading.set(qn('w:fill'),'D9E2F3')
                    properties.append(shading)
                    for run in cell.paragraphs[0].runs:
                        run.bold=True
                for para in cell.paragraphs:
                    para.paragraph_format.space_after=Pt(3)
                    for run in para.runs:
                        run.font.size=Pt(10)
        p('')

    cover=[
        ('ЛЬВІВСЬКИЙ НАЦІОНАЛЬНИЙ УНІВЕРСИТЕТ\nІМЕНІ ІВАНА ФРАНКА',14,65),
        ('ЗВІТ ДО ЛАБОРАТОРНОЇ РОБОТИ №6',16,20),
        ('«Автоматизоване тестування Python-програм»',14,18),
        ('з курсу «Професійний Python»\nВаріант №2 — «Система обліку книг»',14,45),
        ('Виконав: Бровді Олександр\nГрупа: ФеП-32\nПеревірив(ла): Свелеба Сергій Андрійович\nДата: 08.11.2026',12,70),
        ('Львів — 2026',14,0),
    ]
    for i,(text,size,after) in enumerate(cover):
        para=doc.add_paragraph(text,'Title' if i==1 else None)
        para.alignment=WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after=Pt(after)
        for run in para.runs:
            run.font.size=Pt(size)

    page('Мета та тестований проєкт')
    p('Мета — опанувати automated testing із pytest: unit та integration tests, fixtures, parametrization, assertions, exceptions, ізоляцію файлів і середовища, Mock та AsyncMock, statement і branch coverage.')
    p('Варіант 2 — система обліку книг. Реалізовано Book, каталог із пошуком за автором і назвою, фільтрацією за роком, largest book та average pages; CSV import, JSON export, YAML year configuration, BookRepository, report dependency і async external catalog. Реальний integration flow: import → validation → search → export.')
    p('Підсумок: 97 passed, 0 failed; 89 unit cases та 8 integration cases. Покрито 228/228 statements і 44/44 branches. Test suite виявив дефект конфігурації, для якого додано regression test. Сім окремих експериментів показують відмінність виконання коду від перевірки результатів.')
    code('''src/book_catalog/
  models.py, catalog.py, repositories.py, protocols.py
  services.py, config.py, importers.py, exporters.py
  exceptions.py, main.py, __init__.py
tests/conftest.py
tests/unit/
  test_models.py, test_catalog.py, test_services.py
  test_configuration.py, test_importers.py, test_exporters.py
tests/integration/
  test_import_pipeline.py, test_export_pipeline.py
  test_application_flow.py
docs/results/, coverage/html/, TEST_MATRIX.md
docs/Lab_06_Report_Variant_2.docx
Lab_06/report/report.docx''',10)
    p('Запуск: python -m pip install -e ".[dev]", потім python -m pytest -v. Branch coverage, HTML/JSON/XML і поріг 90% увімкнено в pyproject.toml. Для одного файла чи test function доцільно --no-cov, щоб глобальний поріг не застосовувався до підмножини.')

    matrix=[line.split('|')[1:-1] for line in read('docs/TEST_MATRIX.md').splitlines() if line.startswith('|')][2:]
    for number,part in enumerate([matrix[:7],matrix[7:]],1):
        page(f'Матриця тестування частина {number}')
        table(['Компонент','Сценарії','Очікуваний результат'],[[row[0].strip(),row[1].strip(),row[2].strip()] for row in part],[3,7,7])
        p('Повні шляхи відповідних test files наведено в docs/TEST_MATRIX.md. Кожний тест самостійно створює початковий стан. Параметризовані набори включають normal, boundary, empty, invalid, missing, repeated operation і dependency failure.')
        if number==2:
            p('Book приймає непорожні ISBN, title, author; year — ціле 1..9999, pages — ціле > 0. YearPolicy звужує рік до YAML-діапазону. Немає довільної верхньої межі pages; перевірено 1, 2 і 1 000 000. ISBN є ключем каталогу: перевірка контрольної цифри не є вимогою Lab_06.')
            p('Search використовує strip/casefold і підрядок; порожній запит повертає порожній tuple. Порожній каталог має largest=None та average_pages=0.0. При однаковій кількості сторінок largest повертає першу книгу. Дублі ISBN відхиляються.')

    page('Модель Book та unit tests')
    code(read('src/book_catalog/models.py'),8)
    code(function('tests/unit/test_models.py','test_book_creation_preserves_all_domain_fields'),8.5)
    p('Book — immutable dataclass, нормалізує пробіли та захищає основний контракт незалежно від CSV. Об’єкти створюються factory fixture; тести перевіряють повні поля, незмінність і неправильні значення.')

    page('Пошук та обчислення статистики')
    code(read('src/book_catalog/catalog.py'),8.5)
    code(function('tests/unit/test_catalog.py','test_average_pages_keeps_fraction'),9)
    code(function('tests/unit/test_catalog.py','test_empty_catalog_has_defined_neutral_results'),8.5)
    p('Середнє 302/3 перевіряється через pytest.approx. Окремо перевірено case-insensitive author/title search, відсутні результати, invalid filter year, largest tie та duplicate ISBN.')

    page('Fixtures та керування ресурсами')
    for name in ['clean_environment','policy','book_factory','csv_encoding','open_resource']:
        code(function('tests/conftest.py',name),8.5)
    p('book_factory, books, repository, csv_factory і config_path мають function scope: mutable state не ділиться. Лише frozen YearPolicy має module scope. Parameterized fixture перевіряє UTF-8 і UTF-8 з BOM. Autouse fixture ізолює environment, yield fixture закриває handle після тесту.')

    page('Parametrization boundaries та custom exceptions')
    for name in ['test_invalid_book_values_raise_custom_error','test_permitted_year_boundaries','test_year_outside_policy_is_rejected']:
        code(function('tests/unit/test_models.py',name),8)
    p('Мінімум/максимум YearPolicy включні. Значення до та після меж піднімають ValidationError. Перевірка bool потрібна окремо, оскільки bool успадковує int у Python. Параметри мають зрозумілі ids.')

    page('Exception chaining та atomic failure')
    code(function('tests/unit/test_importers.py','test_numeric_conversion_retains_two_level_exception_chain'),8.5)
    code(function('tests/unit/test_exporters.py','test_mid_export_failure_preserves_old_output_and_cleans_temp'),8.5)
    code(function('tests/unit/test_exporters.py','test_context_manager_closes_file_on_exception'),8.5)
    p('pytest.raises перевіряє type та message; exc_info.value дає доступ до cause. Перевірено ImportError → ValidationError → ValueError, збереження старого output, видалення temporary file й закриття file handle при exception. Додатковий test інжектує PermissionError у os.replace через monkeypatch.')

    page('tmp_path та monkeypatch')
    for name in ['test_default_environment','test_environment_override','test_max_year_override']:
        code(function('tests/unit/test_configuration.py',name),9)
    code(function('tests/integration/test_export_pipeline.py','test_import_search_export_matches_author'),8.5)
    p('Файли створюються тільки під tmp_path. Configuration fixtures створюють незалежний YAML і CSV. monkeypatch автоматично скасовує зміни environment та атрибутів. Integration test використовує справжні reader, validator, repository, пошук і JSON exporter.')

    page('Mock return value side effect та interactions')
    code(function('tests/unit/test_services.py','test_report_uses_repository_return_value_and_exports_only_matches'),8.5)
    code(function('tests/unit/test_services.py','test_repository_failure_prevents_export_interaction'),8.5)
    p('Mock(spec=BookRepository) задає repository.all.return_value. create_autospec обмежує сигнатуру exporter; write.return_value перевіряється як результат сервісу. ConnectionError через side_effect має припинити flow до export. Перевірено точні аргументи, кількість викликів та assert_not_called. MagicMock додатково перевіряє iterable contract.')

    page('AsyncMock та async dependency')
    code(function('tests/unit/test_services.py','test_async_external_catalog_success'),8.5)
    code(function('tests/unit/test_services.py','test_async_dependency_failure_does_not_mutate_repository'),8.5)
    p('AsyncMock(spec=ExternalCatalog) моделює асинхронне отримання зовнішніх книг без Інтернету. assert_awaited_once_with перевіряє await, а не лише створення coroutine. Failure зберігає original cause і не викликає repository.add. Весь batch валідується до зміни стану; окремо перевірено malformed record, рік поза політикою та дублікати.')

    page('Інтеграція конфігурації та application flow')
    code(function('tests/integration/test_application_flow.py','test_real_yaml_paths_and_application_pipeline'),8.5)
    code(read('config.yaml'),10)
    picture('application','Рисунок 1. Фактичний запуск застосунку та export двох книг Франка.')
    p('Три integration files містять 8 test cases. Перевіряються YAML paths, UTF-8/BOM, quoted CSV, import → author search → JSON, повторний export та CLI success/failure. У цих тестах файлову систему й JSON parser не замінено mocks.')

    page('Результат повного запуску та coverage')
    picture('coverage','Рисунок 2. Фрагмент фактичного console output pytest з coverage.')
    p('Фінальний suite: 97 passed, 0 failed. Із них 89 unit cases і 8 integration cases, включно з параметризацією. Statement coverage 228/228 = 100%; branch coverage 44/44 = 100%; missing statements/branches = 0. Поріг 90% виконано.')
    p('Зображення сформовано з фактичного виводу, повний журнал — docs/results/tests.txt; JUnit — tests.xml, вимірювання — coverage.json та coverage.xml. Лише декларативні Protocol ellipses і script guard виключено з вимірювання, реалізації застосунку не приховано.')

    page('HTML coverage report та аналіз шляхів')
    html=read('docs/coverage/html/index.html')
    header=re.search(r'<h1>Coverage report:.*?</h1>',html,re.S).group()
    foot=re.search(r'<tfoot>.*?</tfoot>',html,re.S).group()
    code(header+'\n\n'+foot,8)
    p('Наведено справжній фрагмент HTML зі збереженого docs/coverage/html/index.html. Повний HTML-звіт містить переходи до підсвічених source files, functions і classes. JSON підтверджує відсутність missing lines та missing branches.')
    p('100% виміряних переходів не є покриттям усіх поєднань складених умов, усіх платформ чи всіх можливих I/O failures. Реальний зовнішній API не тестується: перевіряється контракт ін’єктованої залежності. Подальший розвиток може додати property-based перевірки пошуку й cross-platform тестування filesystem failures.')
    p('У branch-експерименті спочатку залишався невиконаний перехід medium-condition → small. Додавання pages=50 закрило цей шлях. У production suite відповідні порожні, invalid та failure branches перевірено змістовними assertions.')

    page('Виявлений дефект та regression protection')
    p('Додатковий тест установив input=config.yaml і очікував ConfigurationError. Loader помилково приймав таку конфігурацію: попередня перевірка порівнювала лише input/output та output/config. Це відкладало неправильний тип input до пізнього CSV import замість fail-fast.')
    picture('regression','Рисунок 3. Реальний failure перед виправленням: DID NOT RAISE ConfigurationError.')
    code(function('tests/unit/test_configuration.py','test_config_file_cannot_also_be_input'),9)
    code('''# Before
if incoming == outgoing or outgoing == path.resolve():
    raise ValueError("Input output and config paths must differ")
# After
if len({incoming, outgoing, path.resolve()}) != 3:
    raise ValueError("Input output and config paths must differ")''',9)
    p('Після виправлення цей regression test та весь suite проходять. Before-log збережено окремо; навмисно неправильне середнє з експерименту є навчальною мутацією, а не другим знайденим production defect.')

    evidence=json.loads(read('docs/results/experiments.json'))
    page('Експерименти 1 та 2 слабкі assertions і coverage')
    code(read('docs/experiment_sources/subject.py'),10)
    code(read('docs/experiment_sources/test_weak.py'),10)
    code(read('docs/experiment_sources/test_strong.py'),10)
    table(['Перевірка','Passed','Failed'],[
        ['Weak без assert',1,0],['Strong з approx',0,1]],[9,4,4])
    p('Неправильна функція повертає 100 замість 100.6666667 через floor division. Weak test лише виконує її й має 100% statement coverage, але проходить. Strong test перевіряє контракт середнього й падає. Очікуваний failure ізольовано від основного suite.')
    p('Таким чином execution ≠ verification. Coverage потрібно поєднувати з assertions про повні результати, стан та важливі відсутні interactions.')

    page('Експерименти 3 та 4 branches Mock і fake')
    code(read('docs/experiment_sources/classification.py'),10)
    table(['Набір pages','Branches','Покриття'],[
        ['600, 200','3/4','75%'],['600, 200, 50','4/4','100%']],[9,4,4])
    p('Перший набір проходить large та medium, але не false-перехід другого if. Доданий small-case виконує четвертий перехід. Логи та фактичні counts збережено в experiments.json.')
    code(read('docs/experiment_sources/test_mock_fake.py'),8.5)
    p('Mock зручний для exact interaction і failure injection, але configured return_value не доводить збереження стану. Fake дає природні state assertions і повторне використання; зазвичай менше прив’язує тест до порядку внутрішніх викликів. Обидва приклади пройдено.')

    page('Експерименти 5 6 та 7 ізоляція і failure paths')
    picture('experiments','Рисунок 4. Підсумки семи реально виконаних експериментів.')
    p('Flaky-приклад: 20 random-dependent повторів дали 10 pass і 10 fail. Для відтворення зафіксовано seed 17; це контрольований replay проблеми, а не гарантія для неконтрольованої randomness. Після ін’єкції randint усі 20 тестів стабільно проходять.')
    p('tmp_path isolation: один файловий тест виконано тричі в різних temporary environments. Отримано 3 різні каталоги; snapshots output репозиторію до й після ідентичні. Сам test перевіряє, що output відсутній до запису.')
    p('Failure path: success перевіряє точний result та export arguments; repository failure через side_effect піднімає очікуваний виняток і не викликає exporter. Обидва tests пройдено. Додаткові async failure tests перевіряють absence of mutation.')
    p('Усі навмисні failures запускаються окремим pytest у temporary directory; звичайний test discovery обмежено tests/. Вихідні фрагменти дослідів доступні в docs/experiment_sources, логи — docs/results.')

    qa=json.loads(read('docs/control_answers.json'))
    assert len(qa)==80
    for start in range(0,80,10):
        page(f'Відповіді на контрольні запитання {start+1}–{start+10}')
        for i,(question,answer) in enumerate(qa[start:start+10],start+1):
            para=p('')
            para.paragraph_format.keep_with_next=True
            para.add_run(f'{i}. {question}').bold=True
            p(answer)

    page('Висновок')
    p('Для системи обліку книг за варіантом 2 створено організований pytest suite: 97 test cases перевіряють моделі, пошук, статистику, конфігурацію, CSV/JSON, репозиторій, report service і async external dependency. Fixtures та tmp_path забезпечують незалежність, параметризація охоплює межі, а Mock/AsyncMock відтворюють success і failure без мережі.')
    p('Тести виявили дефект колізії input/config, який виправлено та захищено regression test. Повний запуск проходить з 100% statement і branch coverage. Експерименти підтвердили, що навіть 100% coverage може супроводжувати неправильний результат, якщо немає assertions. Значущі перевірки контрактів залишаються основним критерієм якості.')
    p('Реалізовано більше трьох додаткових можливостей: fixture factory, parameterized/autouse fixtures, custom markers, fake repository, autospec, AsyncMock, failure injection, coverage threshold, тести YAML/env configuration, atomic output, resource cleanup та exception chaining.')
    h('Використані матеріали')
    p('Методичка Lab_06_узгоджено_з_Lab_01.docx, розділи 1–113; вимоги 56–57, експерименти 84–90, структура 102, контрольні запитання 105, звіт 107. Приклади магазину адаптовано до полів і поведінки книг.')
    p('Репозиторій: https://github.com/Olexandr-Brovdi/book-management-system-lab-06')
    doc.core_properties.author='Бровді Олександр'
    doc.core_properties.title='Лабораторна робота 6 Автоматизоване тестування системи обліку книг Варіант 2'
    if ROOT.name=='Lab_06':
        target=ROOT/'report/report.docx'
        target.parent.mkdir(parents=True,exist_ok=True)
        doc.save(target)
    else:
        target=ROOT/'docs/Lab_06_Report_Variant_2.docx'
        doc.save(target)
        canonical=ROOT/'Lab_06/report/report.docx'
        canonical.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(target,canonical)
    print(target)


if __name__=='__main__':
    build()
