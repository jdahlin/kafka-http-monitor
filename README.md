<!-- Begin section: Overview -->

# Kafka HTTP Monitor

![check](https://github.com/github/docs/actions/workflows/check.yml/badge.svg)
![aiven-integration-tests](https://github.com/github/docs/actions/workflows/check.yml/badge.svg)

A small tool to monitor URLs and send the results via Kafka and store them in PostgreSQL.

- 🐍  Uses Python 3.11
- 📦  Uses Pip for dependency management
- 🔌  Uses Asyncio via HTTPx and aiokafka.
- 📊  Pytest for testing.
- 📝  Uses Black for code formatting.
- ⚖️  Uses ruff for linting
- 📦  Integration testing using Aiven.io

How to run
==========

`$ pip install .`
`$ kafka-http-monitor topic url`
`$ kafka-http-copier topic`

Develop
=======

To start developing on this project, first install pre-commit hooks:

`$ pip install pre-commit`
`$ pre-commit install`

Then, install the development dependencies:

`$ pip install -e .[dev]`

You can run the tests via:

`$ pytest src`

You can run the linter via:

`$ ruff`
