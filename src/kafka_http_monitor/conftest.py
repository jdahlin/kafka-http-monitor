"""Pytest fixtures."""
import http

import pytest

from .kafkahelper import KafkaOptions, SaslMechanism, SecurityProtocol
from .url import UrlStats


@pytest.fixture(name="kafka_options")
def kafka_options() -> KafkaOptions:
    """Return Kafka options."""
    return KafkaOptions(
        topics=["test"],
        cluster="localhost:9092",
        security_protocol=SecurityProtocol.PLAINTEXT,
        sasl_mechanism=SaslMechanism.PLAIN,
        sasl_username=None,
        sasl_password=None,
        sasl_certificate=None,
    )


@pytest.fixture
def url_stats() -> UrlStats:
    """Return UrlStats."""
    return UrlStats(
        url="http://localhost",
        method="GET",
        response_status_code=http.HTTPStatus.OK,
        response_time_in_milliseconds=1234,
        response_matched_regex=False,
    )
