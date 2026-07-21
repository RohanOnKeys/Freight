"""
Business logic for Freight secrets.

This module centralizes all secret-related operations used by the Freight
server. Routers delegate to this service instead of interacting directly
with the database or cryptographic helpers.

Responsibilities include:

- Encrypting secrets before persistence.
- Returning public secret metadata.
- Resolving decrypted secrets for runner execution.
- Deleting stored secrets.

Plaintext secret values must never leave this module except when being
returned to an authenticated Freight runner immediately before job
execution.
"""

from sqlalchemy.orm import Session

from freight.core.crypto import decrypt, encrypt
from freight.models.secret import Secret
from freight.schemas.secret import SecretCreate


def create_secret(
    db: Session,
    secret: SecretCreate,
) -> Secret:
    """
    Create and persist a new Freight secret.

    The supplied plaintext value is encrypted before being stored in the
    database.

    Args:
        db:
            Active database session.

        secret:
            Secret creation request.

    Returns:
        Newly created Secret ORM object.
    """

    db_secret = Secret(
        name=secret.name,
        encrypted_value=encrypt(secret.value),
        scope=secret.scope,
    )

    db.add(db_secret)
    db.commit()
    db.refresh(db_secret)

    return db_secret


def list_secrets(
    db: Session,
) -> list[Secret]:
    """
    Retrieve all stored secrets.

    This function returns ORM objects containing encrypted values. Public
    API responses should serialize them using SecretOut so encrypted
    values are never exposed.

    Args:
        db:
            Active database session.

    Returns:
        List of Secret ORM objects.
    """

    return (
        db.query(Secret)
        .order_by(Secret.name)
        .all()
    )


def delete_secret(
    db: Session,
    secret_id: int,
) -> bool:
    """
    Delete a stored secret.

    Args:
        db:
            Active database session.

        secret_id:
            Identifier of the secret to delete.

    Returns:
        True if a secret was deleted, otherwise False.
    """

    secret = db.get(Secret, secret_id)

    if secret is None:
        return False

    db.delete(secret)
    db.commit()

    return True


def resolve_job_secrets(
    db: Session,
    scope: str = "global",
) -> dict[str, str]:
    """
    Resolve decrypted secrets required for job execution.

    The returned mapping is intended only for authenticated Freight
    runners immediately before container startup.

    Args:
        db:
            Active database session.

        scope:
            Secret scope to resolve.

    Returns:
        Dictionary mapping secret names to decrypted plaintext values.
    """

    secrets = (
        db.query(Secret)
        .filter(Secret.scope == scope)
        .all()
    )

    return {
        secret.name: decrypt(secret.encrypted_value)
        for secret in secrets
    }