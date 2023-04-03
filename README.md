<!-- Begin section: Overview -->

# Kafka HTTP Monitor

![check](https://github.com/github/docs/actions/workflows/check.yml/badge.svg)

A small tool to monitor URLs and send the results via Kafka and store them in PostgreSQL.

- 🐍  Uses Python 3.11
- 📦  Uses Pip for dependency management
- 🔌  Uses Asyncio via HTTPx and aiokafka.
- 📊  Pytest for testing.
- 📝  Uses Black for code formatting.
- ⚖️  Uses ruff for linting

How to run
==========

`$ pip install .`
`$ kafka-http-monitor https://www.google.com`

TODO
====

* GHA: run integration test in aiven
