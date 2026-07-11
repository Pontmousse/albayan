"""عميل S3 لمخطوطات BuTeX — document.json وأصول الصور تحت storage_prefix."""

import json
from functools import lru_cache
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException

from app.core.config import settings

DOCUMENT_FILENAME = "document.json"

_UNAVAILABLE = HTTPException(
    status_code=503,
    detail="خدمة التخزين غير مُهيّأة على الخادم.",
)
_FAILED = HTTPException(
    status_code=503,
    detail="تعذّر الوصول إلى خدمة التخزين، حاول مجدداً.",
)
_NOT_FOUND = HTTPException(
    status_code=404,
    detail="الملف غير موجود.",
)


@lru_cache(maxsize=1)
def _client():
    if not settings.s3_bucket:
        raise _UNAVAILABLE
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url or None,
        aws_access_key_id=settings.s3_access_key or None,
        aws_secret_access_key=settings.s3_secret_key or None,
    )


def _object_key(storage_prefix: str, relative_key: str) -> str:
    return f"{storage_prefix.rstrip('/')}/{relative_key.lstrip('/')}"


def _document_key(storage_prefix: str) -> str:
    return _object_key(storage_prefix, DOCUMENT_FILENAME)


def put_json(storage_prefix: str, data: Any) -> None:
    """يكتب document.json تحت storage_prefix."""
    client = _client()
    try:
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=_document_key(storage_prefix),
            Body=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )
    except (BotoCoreError, ClientError) as exc:
        raise _FAILED from exc


def get_json(storage_prefix: str) -> Any:
    """يقرأ document.json من storage_prefix — يعيد None إن لم يوجد بعد."""
    client = _client()
    try:
        response = client.get_object(
            Bucket=settings.s3_bucket,
            Key=_document_key(storage_prefix),
        )
        return json.loads(response["Body"].read())
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return None
        raise _FAILED from exc
    except BotoCoreError as exc:
        raise _FAILED from exc


def put_bytes(
    storage_prefix: str,
    relative_key: str,
    body: bytes,
    content_type: str,
) -> None:
    """يكتب بايتات تحت storage_prefix/relative_key."""
    client = _client()
    try:
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=_object_key(storage_prefix, relative_key),
            Body=body,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError) as exc:
        raise _FAILED from exc


def get_bytes(
    storage_prefix: str, relative_key: str
) -> tuple[bytes, str | None]:
    """يقرأ بايتات من storage_prefix/relative_key — يعيد (body, content_type)."""
    client = _client()
    try:
        response = client.get_object(
            Bucket=settings.s3_bucket,
            Key=_object_key(storage_prefix, relative_key),
        )
        body = response["Body"].read()
        content_type = response.get("ContentType")
        return body, content_type
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            raise _NOT_FOUND from exc
        raise _FAILED from exc
    except BotoCoreError as exc:
        raise _FAILED from exc
