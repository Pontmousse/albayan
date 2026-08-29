"""عميل S3 لمخطوطات BuTeX — document.json وأصول الصور تحت storage_prefix."""

import json
from datetime import datetime
from functools import lru_cache
from typing import Any, TypedDict

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException

from app.core.config import settings

DOCUMENT_FILENAME = "document.json"
COMPILED_PDF = "compiled.pdf"
COMPILE_LOG = "compile.log"

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


def put_json_at(storage_prefix: str, relative_key: str, data: Any) -> None:
    """يكتب JSON تحت storage_prefix/relative_key."""
    client = _client()
    try:
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=_object_key(storage_prefix, relative_key),
            Body=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )
    except (BotoCoreError, ClientError) as exc:
        raise _FAILED from exc


def get_json_at(storage_prefix: str, relative_key: str) -> Any:
    """يقرأ JSON من storage_prefix/relative_key — يعيد None إن لم يوجد."""
    client = _client()
    try:
        response = client.get_object(
            Bucket=settings.s3_bucket,
            Key=_object_key(storage_prefix, relative_key),
        )
        return json.loads(response["Body"].read())
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return None
        raise _FAILED from exc
    except BotoCoreError as exc:
        raise _FAILED from exc


def put_json(storage_prefix: str, data: Any) -> None:
    """يكتب document.json تحت storage_prefix."""
    put_json_at(storage_prefix, DOCUMENT_FILENAME, data)


def get_json(storage_prefix: str) -> Any:
    """يقرأ document.json من storage_prefix — يعيد None إن لم يوجد بعد."""
    return get_json_at(storage_prefix, DOCUMENT_FILENAME)


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


def get_bytes_key(key: str) -> tuple[bytes, str | None]:
    """يقرأ بايتات من مفتاح S3 كامل — يعيد (body, content_type)."""
    client = _client()
    try:
        response = client.get_object(
            Bucket=settings.s3_bucket,
            Key=key,
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


def delete_key(key: str) -> None:
    """يحذف مفتاح S3 واحداً. لا خطأ إن لم يوجد شيء."""
    client = _client()
    try:
        client.delete_object(Bucket=settings.s3_bucket, Key=key)
    except (BotoCoreError, ClientError) as exc:
        raise _FAILED from exc


class ListedObject(TypedDict):
    relative_key: str
    size: int
    last_modified: datetime | None
    content_type: str | None


def list_prefix(
    storage_prefix: str,
    relative_prefix: str = "",
) -> list[ListedObject]:
    """يسرد الكائنات تحت storage_prefix/relative_prefix (بدون document.json إلخ إن لم تكن تحت البادئة)."""
    client = _client()
    normalized = _object_key(storage_prefix, relative_prefix)
    if not normalized.endswith("/"):
        normalized = f"{normalized}/"
    base_len = len(normalized)
    results: list[ListedObject] = []
    try:
        continuation: str | None = None
        while True:
            kwargs: dict[str, Any] = {
                "Bucket": settings.s3_bucket,
                "Prefix": normalized,
            }
            if continuation:
                kwargs["ContinuationToken"] = continuation
            response = client.list_objects_v2(**kwargs)
            for obj in response.get("Contents") or []:
                key = obj.get("Key")
                if not isinstance(key, str) or key.endswith("/"):
                    continue
                relative_key = key[base_len:] if len(key) >= base_len else key
                if not relative_key:
                    continue
                last_modified = obj.get("LastModified")
                results.append(
                    {
                        "relative_key": relative_key,
                        "size": int(obj.get("Size") or 0),
                        "last_modified": last_modified
                        if isinstance(last_modified, datetime)
                        else None,
                        "content_type": None,
                    }
                )
            if not response.get("IsTruncated"):
                break
            continuation = response.get("NextContinuationToken")
    except (BotoCoreError, ClientError) as exc:
        raise _FAILED from exc
    return results


def delete_prefix(prefix: str) -> None:
    """يحذف كل الكائنات تحت البادئة (مثل articles/{id}/). لا خطأ إن لم يوجد شيء."""
    client = _client()
    normalized = prefix if prefix.endswith("/") else f"{prefix}/"
    try:
        continuation: str | None = None
        while True:
            kwargs: dict[str, Any] = {
                "Bucket": settings.s3_bucket,
                "Prefix": normalized,
            }
            if continuation:
                kwargs["ContinuationToken"] = continuation
            response = client.list_objects_v2(**kwargs)
            objects = response.get("Contents") or []
            if objects:
                # S3 يسمح حتى 1000 مفتاحاً في delete_objects
                for start in range(0, len(objects), 1000):
                    chunk = objects[start : start + 1000]
                    client.delete_objects(
                        Bucket=settings.s3_bucket,
                        Delete={
                            "Objects": [{"Key": obj["Key"]} for obj in chunk],
                            "Quiet": True,
                        },
                    )
            if not response.get("IsTruncated"):
                break
            continuation = response.get("NextContinuationToken")
    except (BotoCoreError, ClientError) as exc:
        raise _FAILED from exc
