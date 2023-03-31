"""Producer application for the kafka-http-monitor project."""
import asyncio
import logging
import pickle
import time

import typer
from aiokafka import AIOKafkaProducer

from kafkahelper import SaslMechanism, SecurityProtocol, create_client
from url import probe_url

logger = logging.getLogger(__name__)

def main(  # noqa: PLR0913
        topic: str,
        url: str,
        method: str = "GET",
        times: int = 1,
        wait_in_sections: int = 5,
        kafka_cluster: str = "localhost:9092",
        kafka_sasl_certificate: str = "kafka-ca.cer",
        kakfa_sasl_username: str = "",
        kafka_sasl_password: str = "",
        kafka_security_protocol: SecurityProtocol = SecurityProtocol.PLAINTEXT,
        kafka_sasl_mechanism: SaslMechanism = SaslMechanism.PLAIN,
) -> None:
    """Entry point for producer."""
    last = times + 1

    async def async_main() -> None:
        producer = create_client(
            client_class=AIOKafkaProducer,
            kafka_cluster=kafka_cluster,
            security_protocol=kafka_security_protocol,
            ssl_cafile=kafka_sasl_certificate,
            sasl_username=kakfa_sasl_username or None,
            sasl_password=kafka_sasl_password or None,
            sasl_mechanism=kafka_sasl_mechanism)

        async with producer:
            for i in range(1, last):
                logger.info(f"Probing {method} {url} {i}/{times}")
                url_stats = await probe_url(url=url, method=method)
                await producer.send_and_wait(topic, pickle.dumps(url_stats))
                if i != times:
                    time.sleep(wait_in_sections)

    asyncio.run(async_main())


typer.run(main)
