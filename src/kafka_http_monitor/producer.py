"""Producer application for the kafka-http-monitor project."""
import asyncio
import logging
import pickle
import time

import typer
from aiokafka import AIOKafkaProducer

from kafka_http_monitor.kafkahelper import (
    KafkaOptions,
    SaslMechanism,
    SecurityProtocol,
    create_client,
)
from kafka_http_monitor.url import probe_url

logger = logging.getLogger(__name__)


async def async_main(
    kafka_options: KafkaOptions, wait_in_seconds: int, times: int, url: str, method: str
) -> None:
    """Async main function."""
    producer = create_client(client_class=AIOKafkaProducer, options=kafka_options)
    last = times + 1

    async with producer:
        for i in range(1, last):
            logger.info(f"Probing {method} {url} {i}/{times}")
            url_stats = await probe_url(url=url, method=method)
            for topic in kafka_options.topics:
                await producer.send_and_wait(topic, pickle.dumps(url_stats))
            if i != times:
                time.sleep(wait_in_seconds)


def main(  # noqa: PLR0913
    topics: list[str],
    url: str,
    method: str = "GET",
    times: int = 1,
    wait_in_seconds: int = 5,
    kafka_cluster: str = "localhost:9092",
    kafka_sasl_certificate: str = "kafka-ca.cer",
    kakfa_sasl_username: str = "",
    kafka_sasl_password: str = "",
    kafka_security_protocol: SecurityProtocol = SecurityProtocol.PLAINTEXT,
    kafka_sasl_mechanism: SaslMechanism = SaslMechanism.PLAIN,
) -> None:
    """Entry point for producer."""
    logging.basicConfig(level=logging.INFO)

    kafka_options = KafkaOptions(
        topics=topics,
        cluster=kafka_cluster,
        security_protocol=kafka_security_protocol,
        sasl_mechanism=kafka_sasl_mechanism,
        sasl_username=kakfa_sasl_username or None,
        sasl_password=kafka_sasl_password or None,
        sasl_certificate=kafka_sasl_certificate or None,
    )
    asyncio.run(
        async_main(
            url=url,
            method=method,
            times=times,
            wait_in_seconds=wait_in_seconds,
            kafka_options=kafka_options,
        )
    )


if __name__ == "__main__":
    typer.run(main)
