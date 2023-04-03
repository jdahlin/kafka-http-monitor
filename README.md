<!-- Begin section: Overview -->

# Kafka HTTP Monitor

![check](https://github.com/jdahlin/kafka-http-monitor/actions/workflows/check.yaml/badge.svg)
![aiven-integration-test](https://github.com/jdahlin/kafka-http-monitor/actions/workflows/aiven-integration-test.yaml/badge.svg)

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

To run the monitor which checks a website, use the `kafka-http-monitor` command:
`$ kafka-http-monitor url`

By default, it will run one time and exit. To run several times pass in the `--times` command line option:

`$ kafka-http-monitor --times 10 url`

It waits by 5 seconds between each runs unless you specify another value with `--wait_in_seconds`:

`$ kafka-http-monitor --times 10 --wait_in_seconds 10 url`

To receive the results from kafka and store them in a database use:

`$ kafka-http-copier topic`


By default, both commands will connect to kafka and postgresql installed locally, to connect to a cloud instance,
use a combination of:
*
* --kafka-cluster
* --kafka-security-protocol
* --kafka-sasl-username
* --kafka-sasl-password
* --kafka-sasl-certificate
* --kafka-sasl-mechanism
* --postgresql-url (only for copier)

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
