"""Kafka producer tests."""
import asyncio
import http
import pickle
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import consumer
from consumer import async_main
from kafkahelper import KafkaOptions
from url import UrlStats


@patch("consumer.create_client")
@patch("consumer.connect")
def test_consumer_async_main(connect: AsyncMock,
                             create_client: MagicMock,
                             kafka_options: KafkaOptions,
                             url_stats: UrlStats) -> None:
    """Test the consumer async main function."""
    connect.return_value = sql_conn = AsyncMock()
    create_client.return_value = kafka_consumer = MagicMock()
    kafka_consumer.__aiter__.return_value = [MagicMock(value=pickle.dumps(url_stats))]
    asyncio.run(async_main(kafka_options, "postgresql://localhost"))

    assert sql_conn.mock_calls == [
        call.execute(consumer.SQL_CREATE_TABLES_AND_VIEWS),
        call.fetchrow(consumer.SQL_INSERT_OR_SELECT_URL, "http://localhost"),
        call.fetchrow().__getitem__(0),
        call.copy_records_to_table(
            consumer.RESULT_TABLE,
            records=[(ANY, 1234, http.HTTPStatus.OK, None, False)],
            columns=consumer.RECORD_COLUMNS),
        call.execute("COMMIT"),
        call.close(),
    ]
    assert kafka_consumer.mock_calls == [
        call.__aenter__(),
        call.__aiter__(),
        call.__aexit__(None, None, None),
    ]
