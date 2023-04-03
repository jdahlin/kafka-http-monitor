"""Helper functions for Kafka."""
import enum
from dataclasses import dataclass
from typing import TypeVar, cast

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.helpers import create_ssl_context

T = TypeVar("T", bound=AIOKafkaProducer | AIOKafkaConsumer)


class SecurityProtocol(enum.StrEnum):

    """Security protocols supported by Kafka."""

    PLAINTEXT = enum.auto()
    SASL_PLAINTEXT = enum.auto()
    SASL_SSL = enum.auto()
    SSL = enum.auto()


class SaslMechanism(enum.StrEnum):

    """SASL Mechanisms supported by Kafka."""

    PLAIN = "PLAIN"
    GSSAPI = "GSSAPI"
    SCRAM_SHA_256 = "SCRAM-SHA-256"
    SCRAM_SHA_512 = "SCRAM-SHA-512"
    OAUTHBEARER = "OAUTHBEARER"


@dataclass
class KafkaOptions:

    """Kafka options."""

    topics: list[str]
    cluster: str
    security_protocol: SecurityProtocol
    sasl_mechanism: SaslMechanism
    sasl_username: str | None = None
    sasl_password: str | None = None
    sasl_certificate: str | None = None


def create_client(
    client_class: type[T],
    options: KafkaOptions,
) -> T:
    """Create a Kafka client."""
    ssl_context = None
    if (
        options.security_protocol == SecurityProtocol.SSL
        or options.security_protocol == SecurityProtocol.SASL_SSL
    ):
        ssl_context = create_ssl_context(cafile=options.sasl_certificate)
    return cast(
        T,
        client_class(
            *options.topics,
            bootstrap_servers=options.cluster,
            security_protocol=options.security_protocol.name,
            sasl_mechanism=options.sasl_mechanism,
            sasl_plain_username=options.sasl_username,
            sasl_plain_password=options.sasl_password,
            ssl_context=ssl_context,
        ),
    )
