"""
Pydantic schemas for Freight secrets.

These schemas define the API contract for creating, listing, and
resolving secrets.

Plaintext secret values are accepted only during creation. Once stored,
secret values are never returned through public API responses.

The runner receives decrypted secrets through an internal execution
endpoint immediately before container startup.
"""

from pydantic import BaseModel, ConfigDict


class SecretCreate(BaseModel):
    """
    Request body used to create a new Freight secret.

    Attributes:
        name:
            Unique secret name.

        value:
            Plaintext secret supplied by the user. This value is
            encrypted before being persisted.

        scope:
            Secret scope.

            Examples:
                global
                repository
                organization
        """

    name: str
    value: str
    scope: str


class SecretOut(BaseModel):
    """
    Public representation of a stored secret.

    The encrypted value is intentionally omitted.

    Attributes:
        id:
            Secret identifier.

        name:
            Secret name.

        scope:
            Secret scope.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    scope: str


class JobSecretsOut(BaseModel):
    """
    Internal response returned to Freight runners.

    The mapping contains decrypted environment variables that will be
    injected into the execution container.

    This schema is intended for authenticated runner communication and
    should never be exposed through public APIs.
    """

    secrets: dict[str, str]