# Матриця тестування варіанта 2

| Компонент | Сценарії | Очікування | Тести |
|---|---|---|---|
| Book | normal, empty title/author/isbn, invalid type, pages 0/-1/bool/float | незмінний нормалізований Book або ValidationError | unit/test_models.py |
| Рік | 1799, 1800, 1801, 2025, 2026, 2027; 0, 10000, bool, float | лише межі YearPolicy включно; базовий 1..9999 | unit/test_models.py |
| Сторінки | 0, 1, 2, 1000000, -1, bool, float | pages — додатне ціле без штучної верхньої межі | unit/test_models.py |
| Пошук | author/title substring, різний регістр, пробіли, no match, empty | точний tuple очікуваних книг | unit/test_catalog.py |
| Каталог | рік, largest tie, fractional mean, empty, duplicate | точна книга/tuple, approx(302/3), None/0.0, error | unit/test_catalog.py |
| Repository | empty → add → duplicate, повторне читання | стан зберігається, дубль не додається | unit/test_services.py |
| Report service | repository return_value, exporter result, failure/side_effect | відбір Франка, один виклик, export не викликається після failure | unit/test_services.py |
| Async service | awaited success, network failure, malformed/invalid batch, duplicate | count/state, cause, відсутність часткового додавання | unit/test_services.py |
| Configuration | YAML, missing file/key, wrong schema/range/path, env override/default/missing | Config або ConfigurationError з cause | unit/test_configuration.py; integration/test_application_flow.py |
| Import | correct CSV, UTF-8/BOM, comma/quotes, bad header/number/missing/extra column/quote/file | всі поля Book або ImportError з chain | unit/test_importers.py; integration/test_import_pipeline.py |
| Export | Unicode/all fields, empty, repeated, body failure, replace/create error | валідний JSON, старий файл незмінний, cleanup | unit/test_exporters.py; integration/test_export_pipeline.py |
| Context | відкриття, exception, teardown | файл закрито, temporary output видалено | unit/test_exporters.py; conftest.py |
| Full pipeline | YAML → CSV → Book → search → JSON; CLI success/failure | точний JSON Франка та exit code 1 при configuration failure | integration/test_application_flow.py; test_export_pipeline.py |

Межі для оцінок 0..100 з методички адаптовано до року/сторінок книг.
Стан каталогу перевіряється незалежно в кожному тесті; pytest fixtures не
передають mutable state між тестами. Закритий контракт пошуку — підрядок,
casefold і strip; порожній запит означає відсутність збігів.
