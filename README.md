uv run pytest tests/test_phones.py        # только один файл
uv run pytest -v                          # каждый тест отдельной строкой, с PASSED/FAILED
uv run pytest -k e164                     # только тесты, в имени которых есть "e164"
uv run pytest -x                          # остановиться на первом упавшем
uv run pytest -s                          # показывать print() из тестов (по умолчанию скрыт)