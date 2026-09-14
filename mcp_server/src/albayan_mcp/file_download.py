"""Bounded retrieval of a client-authorized temporary file URL."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from dataclasses import dataclass

import httpx


# httpx's INFO request log includes the full URL, including signed query data.
logging.getLogger("httpx").setLevel(logging.WARNING)


MAX_IMAGE_BYTES = 5 * 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 15.0
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


@dataclass(frozen=True)
class DownloadedImage:
    content: bytes
    content_type: str
    filename: str


def _media_type(value: str | None) -> str | None:
    normalized = (value or "").split(";", 1)[0].strip().lower()
    return normalized or None


async def _assert_public_host(host: str, port: int) -> None:
    try:
        rows = await asyncio.to_thread(
            socket.getaddrinfo,
            host,
            port,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise RuntimeError("تعذّر الوصول إلى ملف الصورة المؤقت.") from exc

    addresses = {
        ipaddress.ip_address(row[4][0].split("%", 1)[0])
        for row in rows
        if row[4]
    }
    if not addresses or any(not address.is_global for address in addresses):
        raise RuntimeError("رابط ملف الصورة غير مسموح.")


async def download_client_image(
    download_url: str,
    *,
    declared_content_type: str | None,
) -> DownloadedImage:
    """Download one public HTTPS image without forwarding Albayan credentials."""
    if len(download_url) > 4096:
        raise RuntimeError("رابط ملف الصورة غير صالح.")
    try:
        url = httpx.URL(download_url)
    except Exception as exc:
        raise RuntimeError("رابط ملف الصورة غير صالح.") from exc
    if (
        url.scheme != "https"
        or not url.host
        or bool(url.username)
        or bool(url.password)
        or url.fragment
    ):
        raise RuntimeError("يجب أن يستخدم ملف الصورة رابط HTTPS مؤقتاً وآمناً.")

    declared = _media_type(declared_content_type)
    if declared is not None and declared not in ALLOWED_IMAGE_TYPES:
        raise RuntimeError("نوع ملف الصورة غير مدعوم.")

    await _assert_public_host(url.host, url.port or 443)
    timeout = httpx.Timeout(DOWNLOAD_TIMEOUT_SECONDS)
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            async with client.stream(
                "GET",
                url,
                headers={"Accept": "image/jpeg,image/png,image/gif,image/webp"},
            ) as response:
                if response.is_redirect:
                    raise RuntimeError("رابط ملف الصورة أعاد التوجيه بصورة غير مسموحة.")
                if response.status_code >= 400:
                    raise RuntimeError("تعذّر تنزيل ملف الصورة المؤقت.")

                raw_length = response.headers.get("content-length")
                if raw_length:
                    try:
                        content_length = int(raw_length)
                    except ValueError:
                        content_length = -1
                    if content_length > MAX_IMAGE_BYTES:
                        raise RuntimeError("حجم الصورة يتجاوز الحد المسموح (5 ميغابايت).")

                response_type = _media_type(response.headers.get("content-type"))
                if response_type == "application/octet-stream":
                    response_type = None
                if response_type is not None and response_type not in ALLOWED_IMAGE_TYPES:
                    raise RuntimeError("نوع ملف الصورة غير مدعوم.")
                if declared and response_type and declared != response_type:
                    raise RuntimeError("نوع ملف الصورة لا يطابق محتواه.")
                content_type = response_type or declared
                if content_type is None:
                    raise RuntimeError("تعذّر تحديد نوع ملف الصورة.")

                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_IMAGE_BYTES:
                        raise RuntimeError("حجم الصورة يتجاوز الحد المسموح (5 ميغابايت).")
    except httpx.HTTPError as exc:
        raise RuntimeError("تعذّر تنزيل ملف الصورة المؤقت.") from exc

    if not body:
        raise RuntimeError("ملف الصورة فارغ.")
    return DownloadedImage(
        content=bytes(body),
        content_type=content_type,
        filename=f"upload{ALLOWED_IMAGE_TYPES[content_type]}",
    )
