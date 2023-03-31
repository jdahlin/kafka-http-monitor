"""Kafka producer tests."""
import asyncio
import pickle
from unittest.mock import AsyncMock, MagicMock, call, patch

from aiokafka import AIOKafkaProducer

from src import producer
from src.kafkahelper import KafkaOptions
from src.producer import async_main
from src.url import UrlStats


@patch(f"{producer.__name__}.create_client")
@patch(f"{producer.__name__}.probe_url")
def test_async_main(probe_url: AsyncMock,
                    create_client: MagicMock,
                    kafka_options: KafkaOptions,
                    url_stats: UrlStats) -> None:
    """Test the consumer async main function."""
    probe_url.return_value = url_stats
    producer = MagicMock(
        client_class=AIOKafkaProducer,
        options=kafka_options,
    )
    create_client.return_value = producer
    producer.send_and_wait = AsyncMock()

    asyncio.run(async_main(kafka_options, 1, 1, "http://localhost", "GET"))

    assert probe_url.mock_calls == [
        call(url="http://localhost", method="GET"),
    ]
    assert create_client.mock_calls == [
        call(client_class=AIOKafkaProducer, options=kafka_options),
        call().__aenter__(),
        call().send_and_wait("test", pickle.dumps(url_stats)),
        call().__aexit__(None, None, None),
    ]
