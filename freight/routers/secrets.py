"""
REST API for Freight secrets.

This router exposes endpoints for managing encrypted secrets used during
pipeline execution.

Plaintext secret values are accepted only when creating a secret. Public
responses never expose stored secret values.

All business logic is delegated to freight.services.secret_service.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from freight.database import get_db
from freight.schemas.secret import (
    JobSecretsOut,
    SecretCreate,
    SecretOut,
)
from freight.services.secret_service import (
    create_secret,
    delete_secret,
    list_secrets,
    resolve_job_secrets,
)

router = APIRouter(
    prefix="/secrets",
    tags=["Secrets"],
)


@router.post(
    "",
    response_model=SecretOut,
    status_code=status.HTTP_201_CREATED,
)
def create_secret_endpoint(
    secret: SecretCreate,
    db: Session = Depends(get_db),
) -> SecretOut:
    """
    Create a new encrypted secret.

    The supplied plaintext value is encrypted before being persisted.

    Args:
        secret:
            Secret creation request.

        db:
            Active database session.

    Returns:
        Metadata describing the newly created secret.
    """

    return create_secret(
        db=db,
        secret=secret,
    )


@router.get(
    "",
    response_model=list[SecretOut],
)
def list_secrets_endpoint(
    db: Session = Depends(get_db),
) -> list[SecretOut]:
    """
    List all stored secrets.

    Secret values are intentionally omitted from the response.

    Args:
        db:
            Active database session.

    Returns:
        List of stored secret metadata.
    """

    return list_secrets(db)


@router.delete(
    "/{secret_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_secret_endpoint(
    secret_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Delete a stored secret.

    Args:
        secret_id:
            Identifier of the secret to remove.

        db:
            Active database session.

    Raises:
        HTTPException:
            If the requested secret does not exist.

    Returns:
        Empty response indicating successful deletion.
    """

    deleted = delete_secret(
        db=db,
        secret_id=secret_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found.",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.get(
    "/resolve",
    response_model=JobSecretsOut,
)
def resolve_secrets_endpoint(
    scope: str = "global",
    db: Session = Depends(get_db),
) -> JobSecretsOut:
    """
    Resolve decrypted secrets for runner execution.

    This endpoint is intended for authenticated Freight runners. The
    returned values are injected into the execution container as
    environment variables.

    Args:
        scope:
            Secret scope to resolve.

        db:
            Active database session.

    Returns:
        Mapping of environment variable names to decrypted values.
    """

    return JobSecretsOut(
        secrets=resolve_job_secrets(
            db=db,
            scope=scope,
        )
    )