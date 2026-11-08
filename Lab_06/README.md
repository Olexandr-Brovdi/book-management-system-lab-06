# Система обліку книг

Лабораторна робота №6 «Автоматизоване тестування Python-програм».
**Варіант 2. Бровді Олександр, ФеП-32.** Курс «Професійний Python».

## Встановлення та запуск

Python 3.11+. З кореня репозиторію або автономного каталогу `Lab_06`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -v
book-catalog --config config.yaml --author Франко
```

Linux/macOS: `source .venv/bin/activate`. Усі 97 тестів запускаються однією
командою `python -m pytest`. Звіт HTML створюється в `htmlcov/index.html`,
також формуються JSON і XML та таблиця пропущених рядків у консолі.
Поріг 90% і branch coverage налаштовано у `pyproject.toml`.

```text
python -m pytest -m unit --no-cov
python -m pytest -m integration --no-cov
python -m pytest tests/unit/test_catalog.py --no-cov
python -m pytest tests/unit/test_catalog.py::test_average_pages_keeps_fraction --no-cov
```

Для окремої підмножини `--no-cov` прибирає загальний поріг покриття, оскільки
один тест не повинен покривати весь застосунок. Повний запуск зберігає поріг.

## Поведінка та структура

Book перевіряє непорожні ISBN/назву/автора, цілий рік 1..9999 і додатні цілі
сторінки; bool/float замість int не приймаються. ISBN у цій роботі є непорожнім
ключем; перевірка його контрольної цифри не входить до контракту Lab_06.
YearPolicy із YAML додатково обмежує допустимий діапазон років. Значення
2026 задано явно, тести не залежать від поточної дати.

Catalog підтримує пошук підрядка за автором і назвою без урахування регістру,
фільтрацію за роком, найбільшу книгу (при рівності перша), середню кількість
сторінок. Порожній запит повертає порожній результат, порожній каталог —
`None` для найбільшої книги та `0.0` для середнього. Дублікати ISBN заборонено.

CSV → validation → repository → author search → atomic JSON export — реальна
інтеграція з тимчасовими файлами в тестах. Відносні шляхи прив’язано до YAML.
`BOOK_MAX_YEAR` перевизначає верхній рік, `BOOK_ENV` — середовище запуску.
AsyncCatalogService одержує зовнішній каталог через ін’єкцію залежності,
перевіряє всю партію до додавання й обробляє failure зі збереженням cause.
Реальний Інтернет у тестах не використовується.

```text
src/book_catalog/
  models.py, catalog.py, config.py, exceptions.py
  protocols.py, repositories.py, services.py
  importers.py, exporters.py, main.py
tests/
  conftest.py
  unit/test_models.py, test_catalog.py, test_services.py
  unit/test_configuration.py, test_exporters.py, test_importers.py
  integration/test_import_pipeline.py, test_export_pipeline.py
  integration/test_application_flow.py
data/books.csv, config.yaml, pyproject.toml
tools/run_experiments.py, create_report_assets.py, build_report.py
tools/validate_submission.py
docs/TEST_MATRIX.md, results/, experiment_sources/, coverage/html/
docs/Lab_06_Report_Variant_2.docx
Lab_06/ — автономна копія, канонічний звіт report/report.docx
```

## Тестування та результати

97 пройдених test cases: 89 unit та 8 integration; це включає параметризовані
випадки, а не 97 окремих functions. 228/228 statements і 44/44 branches виконано.
Виключено лише декларативні тіла Protocol (`...`) та script guard.
100% coverage не означає перевірку всіх комбінацій умов або відсутність bugs.

Повна матриця — `docs/TEST_MATRIX.md`. Реалізовано factory, parameterized і
autouse fixtures; function/module scopes, yield teardown, pytest.approx,
pytest.raises, tmp_path, monkeypatch, Mock/spec/autospec/MagicMock/AsyncMock,
return_value, side_effect, awaited та звичайні interaction assertions.
Перевірено context manager cleanup, exception chaining та atomic failure.

Виявлений дефект: `input == config.yaml` не відхилявся loader-ом. Додано
regression test і перевірку різних input/output/config. Результат до виправлення
збережено в `docs/results/regression_before_fix.txt`; повний suite після — tests.txt.

## Сім експериментів

```text
python tools/run_experiments.py
```

1. Слабкий тест пропускає навмисно неправильне ціле середнє 100 замість
   100.6667; сильний тест із approx падає.
2. Той самий неправильний код має 100% statement coverage без assertions.
3. Класифікація книг за pages: після додавання small-case branch coverage
   зростає з 3/4 (75%) до 4/4 (100%).
4. Mock перевіряє виклик, fake — накопичений стан; обидва приклади проходять.
5. 20 повторів неправильного random-dependent test дають 10 pass/10 fail.
   Seed 17 фіксує відтворювану послідовність експерименту. Після підміни
   джерела randomness усі 20 проходять і не залежать від shared random state.
6. Три запуски файлового тесту мають три різні tmp_path; output репозиторію
   не змінюється.
7. Success/failure зовнішньої залежності: перевірено результат та відсутність
   export після помилки repository.

Навмисно неправильні експериментальні приклади розміщено поза `tests/`.
Вони запускаються в окремих temporary directories, очікувані failures
не є failures основного suite. Вихідні коди, логи й підсумки — у docs/results.

## Звіт і відтворення

Звіт містить усі 80 відповідей, матрицю, приклади коду, actual test output,
statement/branch coverage, фрагмент HTML, аналіз обмежень і сім експериментів.
Для його перебудови з кореня:

```text
python -m pip install -e ".[dev,report]"
python tools/create_report_assets.py
python tools/build_report.py
python tools/validate_submission.py
```

Збережений HTML звіт — `docs/coverage/html/index.html`. Звіти Lab_01–05 у
новому репозиторії відсутні. Дві копії DOCX ідентичні та відповідають варіанту 2.
