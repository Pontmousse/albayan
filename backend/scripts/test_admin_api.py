#!/usr/bin/env python3
"""اختبار ذكي لمسارات Admin API.

كيفية الحصول على التوكنات:
  1. سجّل دخولاً في الواجهة كـ admin وكمستخدم عادي.
  2. من DevTools → Network انسخ قيمة Authorization Bearer لأي طلب API،
     أو من Application/Cookies حسب إعداد Clerk.

التشغيل:
  ADMIN_TOKEN=... NON_ADMIN_TOKEN=... \\
  API_BASE=http://localhost:8000 \\
  python scripts/test_admin_api.py

اختياري:
  REVIEWER_USER_ID=<uuid>   لتعيين مراجع موجود مباشرة
  INVITE_EMAIL=someone@example.com  لتجربة إنشاء دعوة (بدون Resend تُعاد warning)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

API_BASE = os.environ.get("API_BASE", "http://localhost:8000").rstrip("/")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
NON_ADMIN_TOKEN = os.environ.get("NON_ADMIN_TOKEN", "")
REVIEWER_USER_ID = os.environ.get("REVIEWER_USER_ID", "")
INVITE_EMAIL = os.environ.get("INVITE_EMAIL", "invite-test@example.com")


class StepError(Exception):
    pass


def request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    expect_status: int | None = None,
) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            payload: Any = json.loads(raw) if raw else None
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {"detail": raw}
        except json.JSONDecodeError:
            payload = {"detail": raw}
        status = exc.code
    except urllib.error.URLError as exc:
        raise StepError(f"تعذّر الاتصال بـ {API_BASE}: {exc}") from exc

    if expect_status is not None and status != expect_status:
        raise StepError(
            f"{method} {path} → {status} (متوقع {expect_status}): {payload}"
        )
    return status, payload


def step(name: str, fn) -> None:
    try:
        fn()
        print(f"PASS  {name}")
    except Exception as exc:
        print(f"FAIL  {name}: {exc}")
        raise


def main() -> int:
    if not ADMIN_TOKEN or not NON_ADMIN_TOKEN:
        print(
            "حدّد ADMIN_TOKEN و NON_ADMIN_TOKEN في البيئة قبل التشغيل.",
            file=sys.stderr,
        )
        return 2

    failures = 0

    def run(name: str, fn) -> None:
        nonlocal failures
        try:
            step(name, fn)
        except Exception:
            failures += 1

    run(
        "health",
        lambda: request("GET", "/health", expect_status=200),
    )

    run(
        "non-admin gets 403 on /admin/articles",
        lambda: request(
            "GET",
            "/api/v1/admin/articles",
            token=NON_ADMIN_TOKEN,
            expect_status=403,
        ),
    )

    articles_holder: dict[str, Any] = {}

    def list_as_admin() -> None:
        status, payload = request(
            "GET",
            "/api/v1/admin/articles",
            token=ADMIN_TOKEN,
            expect_status=200,
        )
        assert isinstance(payload, list), payload
        articles_holder["articles"] = payload

    run("admin lists articles", list_as_admin)

    run(
        "admin lists users",
        lambda: request(
            "GET", "/api/v1/admin/users", token=ADMIN_TOKEN, expect_status=200
        ),
    )

    created: dict[str, Any] = {}

    def create_article() -> None:
        _, payload = request(
            "POST",
            "/api/v1/articles",
            token=ADMIN_TOKEN,
            body={"title": "مقال اختبار إداري", "abstract": "اختبار"},
            expect_status=201,
        )
        created["article_id"] = payload["id"]

    run("admin creates article as author", create_article)

    article_id = created.get("article_id")

    if article_id and REVIEWER_USER_ID:
        run(
            "assign reviewer by user_id",
            lambda: request(
                "POST",
                f"/api/v1/admin/articles/{article_id}/assign-reviewer",
                token=ADMIN_TOKEN,
                body={"user_id": REVIEWER_USER_ID},
                expect_status=201,
            ),
        )
        run(
            "unassign reviewer",
            lambda: request(
                "DELETE",
                f"/api/v1/admin/articles/{article_id}/reviewers/{REVIEWER_USER_ID}",
                token=ADMIN_TOKEN,
                expect_status=204,
            ),
        )

    if article_id:
        invite_holder: dict[str, Any] = {}

        def invite() -> None:
            _, payload = request(
                "POST",
                f"/api/v1/admin/articles/{article_id}/invite",
                token=ADMIN_TOKEN,
                body={"email": INVITE_EMAIL, "role": "reviewer"},
                expect_status=201,
            )
            assert payload.get("invitation"), payload
            invite_holder["id"] = payload["invitation"]["id"]
            # بدون Resend يُفترض warning وليس فشل إنشاء السجل
            print(f"      invite warning={payload.get('warning')!r}")

        run("create invitation record", invite)

        if invite_holder.get("id"):
            run(
                "cancel invitation",
                lambda: request(
                    "DELETE",
                    f"/api/v1/admin/invitations/{invite_holder['id']}",
                    token=ADMIN_TOKEN,
                    expect_status=204,
                ),
            )

        def override() -> None:
            _, payload = request(
                "POST",
                f"/api/v1/admin/articles/{article_id}/override-decision",
                token=ADMIN_TOKEN,
                body={"status": "under_review", "reason": "اختبار تجاوز"},
                expect_status=200,
            )
            assert payload["status"] == "under_review", payload
            _, detail = request(
                "GET",
                f"/api/v1/admin/articles/{article_id}",
                token=ADMIN_TOKEN,
                expect_status=200,
            )
            assert detail["current_version"]["status"] == "under_review", detail

        run("override-decision updates current version status", override)

    if failures:
        print(f"\n{failures} step(s) failed.")
        return 1
    print("\nAll steps passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
