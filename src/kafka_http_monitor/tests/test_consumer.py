"""Kafka producer tests."""
import asyncio
import dataclasses
import http
import json
import logging
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

from _pytest.logging import LogCaptureFixture

from kafka_http_monitor.consumer import (
    RECORD_COLUMNS,
    RESULT_TABLE,
    SQL_CREATE_TABLES_AND_VIEWS,
    SQL_INSERT_OR_SELECT_URL,
    async_main,
)
from kafka_http_monitor.kafkahelper import KafkaOptions
from kafka_http_monitor.url import UrlStats


@patch("kafka_http_monitor.consumer.create_client")
@patch("kafka_http_monitor.consumer.connect")
def test_consumer_async_main(
    connect: AsyncMock,
    create_client: MagicMock,
    kafka_options: KafkaOptions,
    url_stats: UrlStats,
    caplog: LogCaptureFixture,
) -> None:
    """Test the consumer async main function."""
    connect.return_value = sql_conn = AsyncMock()
    create_client.return_value = kafka_consumer = MagicMock()
    kafka_consumer.__aiter__.return_value = [
        MagicMock(value=json.dumps(dataclasses.asdict(url_stats))),
    ]
    with caplog.at_level(logging.INFO):
        asyncio.run(async_main(kafka_options, "postgresql://localhost", 0))
    assert caplog.record_tuples == [
        ("kafka_http_monitor.consumer", 20, "Connected to db, creating DDL"),
        ("kafka_http_monitor.consumer", 20, "DDL created"),
        ("kafka_http_monitor.consumer", 20, "Connected to kafka"),
        ("kafka_http_monitor.consumer", 20, "polling messages"),
        (
            "kafka_http_monitor.consumer",
            20,
            'MESSAGE! {"url": "http://localhost", "method": "GET", '
            '"response_time_in_milliseconds": 1234, "response_status_code": 200, '
            '"regex": null, "response_matched_regex": false} 1',
        ),
    ]

    assert sql_conn.mock_calls == [
        call.execute(SQL_CREATE_TABLES_AND_VIEWS),
        call.fetchrow(SQL_INSERT_OR_SELECT_URL, "http://localhost"),
        call.fetchrow().__getitem__(0),
        call.copy_records_to_table(
            RESULT_TABLE,
            records=[(ANY, 1234, http.HTTPStatus.OK, None, False)],
            columns=RECORD_COLUMNS,
        ),
        call.execute("COMMIT"),
        call.close(),
    ]
    assert kafka_consumer.mock_calls == [
        call.__aenter__(),
        call.__aiter__(),
        call.__aexit__(None, None, None),
    ]
