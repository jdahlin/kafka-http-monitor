"""Consumer for Kafka messages."""
import asyncio
import http
import logging
import pickle
from re import Pattern
from typing import TYPE_CHECKING, cast, NewType, Any

import asyncpg
import typer
from aiokafka import AIOKafkaConsumer, ConsumerRecord

from kafkahelper import SaslMechanism, SecurityProtocol, create_client

if TYPE_CHECKING:
    from url import UrlStats

logger = logging.getLogger(__name__)
ResultTuple = tuple[int | None, int, http.HTTPStatus | None, int | None, bool]
UrlId = NewType('UrlId', int)
RegexId = NewType('RegexId', int)
regex_cache: dict[Pattern[str], RegexId] = {}
url_cache: dict[str, UrlId] = {}

SQL_CREATE_TABLES_AND_VIEWS = """
CREATE TABLE IF NOT EXISTS regex (
    -- can store up to 2147483647 regexes
    id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

    -- the actual regex, for example: ^[a-z]+$
    regex TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS url (
    -- can store up to 2147483647 urls
    id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

    -- a url
    url TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS result (
    -- can store up to 9223372036854775807 (2^63)-1 results
    -- In practice that means you can store 1 billion rows per second for 292 years
    -- 9223372036854775807 / 86400 / 365 / 24 / 60 / 60 / 1_000_000_000 = 292.471
    id INT8 GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- when the regex was created, for example: 2021-01-01 00:00:00
    created_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),

    -- the url that was tested, for example: https://example.com
    -- This is an optimization that assumes that urls are longer than 4 characters
    url_id INT NOT NULL,

    -- the response time in milliseconds, for example: 123
    response_time INTEGER NOT NULL,

    -- the status code, for example: 200
    -- NULL indicates that the request failed
    status_code INTEGER NULL,

    -- a reference to the regex that was used
    -- This is an optimization that assumes that regexes are longer than 4 characters
    -- NULL indicates that no regex was used
    regex_id SMALLINT REFERENCES regex(id),

    -- whether the regex matched the url, for example: true
    regex_match BOOLEAN
);

-- A view that joins the result table with the url and regex tables
CREATE OR REPLACE VIEW result_view AS
SELECT
    result.id,
    result.created_at,
    result.response_time,
    result.status_code,
    url.url,
    regex.regex,
    result.regex_match
FROM result
JOIN url ON result.url_id = url.id
LEFT JOIN regex ON result.regex_id = regex.id;
"""
SQL_INSERT_OR_SELECT_REGEX = """
WITH insert_regex AS(
    INSERT INTO regex (regex)
    SELECT $1 WHERE NOT EXISTS (SELECT 1 FROM regex r WHERE r.regex = $1)
    ON CONFLICT (regex) DO NOTHING
    RETURNING id
)
SELECT * FROM insert_regex
UNION
SELECT id FROM regex WHERE regex = $1;
"""
SQL_INSERT_OR_SELECT_URL = """
WITH insert_url AS(
    INSERT INTO url (url)
    SELECT $1 WHERE NOT EXISTS (SELECT 1 FROM url u WHERE u.url = $1)
    ON CONFLICT("url") DO NOTHING
    RETURNING id
)
SELECT id FROM url WHERE url = $1
UNION
SELECT * FROM insert_url;
"""
RECORD_COLUMNS = [
    "url_id",
    "response_time",
    "status_code",
    "regex_id",
    "regex_match",
]
RESULT_TABLE = "result"


async def insert_or_select_regex(sql_conn: asyncpg.Connection[Any],
                                 regex: Pattern[str] | None) -> int | None:
    """Insert or select a regex from the database."""
    if not regex:
        return None
    regex_id = regex_cache.get(regex)
    if regex_id:
        return regex_id
    result = await sql_conn.fetchrow(SQL_INSERT_OR_SELECT_REGEX, regex)
    if result is None:
        return regex_id
    regex_id = regex_cache[regex] = cast(RegexId, result[0])
    return regex_id

async def insert_or_select_url(sql_conn: asyncpg.Connection[Any], url: str) -> int | None:
    """Insert or select an url from the database."""
    url_id = url_cache.get(url)
    if url_id is None:
        result = (await sql_conn.fetchrow(SQL_INSERT_OR_SELECT_URL, url))
        if result is not None:
            url_id = cast(UrlId, result[0])
            url_cache[url] = url_id
    return url_id

async def parse_message(sql_conn: asyncpg.Connection[Any], message: ConsumerRecord) -> ResultTuple:
    """Parse a Kafka message."""
    url_stats: "UrlStats" = pickle.loads(message.value)  # noqa: S301
    regex_id = await insert_or_select_regex(sql_conn, url_stats.regex)
    url_id = await insert_or_select_url(sql_conn, url_stats.url)
    return (
        url_id,
        url_stats.response_time_in_milliseconds,
        url_stats.response_status_code,
        regex_id,
        url_stats.response_matched_regex,
    )


def main(  # noqa: PLR0913
        topic: str,
        kafka_cluster: str = "localhost:9092",
        kafka_sasl_certificate: str = "kafka-ca.cer",
        kafka_sasl_mechanism: SaslMechanism = SaslMechanism.PLAIN,
        kakfa_sasl_username: str = "",
        kafka_sasl_password: str = "",
        kafka_security_protocol: SecurityProtocol = SecurityProtocol.PLAINTEXT,
        postgresql_url: str = "postgresql://postgres@localhost/postgres",
) -> None:
    """Entry point for consumer.

    This function will connect as a consumer to Kafka and insert
    the messages into a PostgreSQL database.
    """
    logging.basicConfig(level=logging.INFO)

    async def async_main() -> None:
        """Async main function."""
        consumer = create_client(
            topic,
            client_class=AIOKafkaConsumer,
            kafka_cluster=kafka_cluster,
            security_protocol=kafka_security_protocol,
            ssl_cafile=kafka_sasl_certificate,
            sasl_username=kakfa_sasl_username or None,
            sasl_password=kafka_sasl_password or None,
            sasl_mechanism=kafka_sasl_mechanism)

        sql_conn = await asyncpg.connect(postgresql_url)
        logger.info("Connected to db, creating DDL")

        await sql_conn.execute(SQL_CREATE_TABLES_AND_VIEWS)
        logger.info("DDL created")

        async with consumer:
            logger.info("Connected to kafka")

            logger.info("polling messages")
            async for message in consumer:
                logger.info("MESSAGE! %s", message)
                record = await parse_message(sql_conn, message)
                await sql_conn.copy_records_to_table(
                    RESULT_TABLE,
                    records=[record],
                    columns=RECORD_COLUMNS,
                )
                await sql_conn.execute("COMMIT")

        await sql_conn.close()

    asyncio.run(async_main())


typer.run(main)
