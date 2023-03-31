"""Helper functions for Kafka."""
import enum
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


def create_client(
        *topics: str,
        client_class: type[T],
        kafka_cluster: str,
        security_protocol: SecurityProtocol,
        ssl_cafile: str | None = None,
        sasl_username: str | None = None,
        sasl_password: str | None = None,
        sasl_mechanism: SaslMechanism | None = SaslMechanism.PLAIN,
) -> T:
    """Create a Kafka client."""
    ssl_context = None
    if (security_protocol == SecurityProtocol.SSL or
        security_protocol == SecurityProtocol.SASL_SSL):
        ssl_context = create_ssl_context(cafile=ssl_cafile)
    return cast(T, client_class(
        *topics,
        bootstrap_servers=kafka_cluster,
        security_protocol=security_protocol.name,
        sasl_mechanism=sasl_mechanism,
        sasl_plain_username=sasl_username,
        sasl_plain_password=sasl_password,
        ssl_context=ssl_context,
    ))
