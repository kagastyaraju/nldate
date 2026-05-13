# nldate

A Python library for parsing natural-language date strings into `datetime.date` objects.

## Install

```bash
uv sync
```

## Usage

```python
from datetime import date
from nldate import parse

parse("today")                                    # date.today()
parse("tomorrow")                                 # today + 1 day
parse("next Tuesday")                            # next Tuesday
parse("in 3 days")                               # today + 3 days
parse("5 days ago")                              # today - 5 days
parse("5 days before December 1st, 2025")        # 2025-11-26
parse("1 year and 2 months after yesterday")     # yesterday + 1yr 2mo
parse("2024-01-05")                              # 2024-01-05
```

The optional `today` parameter sets the reference date for relative expressions:

```python
parse("next Monday", today=date(2025, 5, 14))
```

## Development

```bash
uv run pytest          # run tests
uv run mypy src tests  # type check
uv run ruff check .    # lint
uv run ruff format .   # format
```
