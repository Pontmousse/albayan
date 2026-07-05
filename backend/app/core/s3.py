"""عميل S3 بسيط لمخطوطات BuTeX — put/get لملف document.json فقط."""

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


def _document_key(storage_prefix: str) -> str:
    return f"{storage_prefix.rstrip('/')}/{DOCUMENT_FILENAME}"


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
