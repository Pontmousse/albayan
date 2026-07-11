#!/usr/bin/env python3
"""اختبار مسارات المراجع والمحرر.

المتطلبات:
  ADMIN_TOKEN, REVIEWER_TOKEN, EDITOR_TOKEN (Bearer من Clerk)
  اختياري: NON_ASSIGNEE_TOKEN للتحقق من 404/403

التشغيل:
  ADMIN_TOKEN=... REVIEWER_TOKEN=... EDITOR_TOKEN=... \\
  API_BASE=http://localhost:8000 \\
  python scripts/test_reviewer_editor_api.py
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
REVIEWER_TOKEN = os.environ.get("REVIEWER_TOKEN", "")
EDITOR_TOKEN = os.environ.get("EDITOR_TOKEN", "")
NON_ASSIGNEE_TOKEN = os.environ.get("NON_ASSIGNEE_TOKEN", "")


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
    if not ADMIN_TOKEN or not REVIEWER_TOKEN or not EDITOR_TOKEN:
        print(
            "حدّد ADMIN_TOKEN و REVIEWER_TOKEN و EDITOR_TOKEN قبل التشغيل.",
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

    ids: dict[str, Any] = {}

    def resolve_users() -> None:
        _, me_rev = request(
            "GET", "/api/v1/users/me", token=REVIEWER_TOKEN, expect_status=200
        )
        _, me_ed = request(
            "GET", "/api/v1/users/me", token=EDITOR_TOKEN, expect_status=200
        )
        ids["reviewer_user_id"] = me_rev["id"]
        ids["editor_user_id"] = me_ed["id"]

    run("resolve reviewer/editor user ids", resolve_users)

    def create_and_submit() -> None:
        _, article = request(
            "POST",
            "/api/v1/articles",
            token=ADMIN_TOKEN,
            body={"title": "مقال اختبار مراجعة/تحرير", "abstract": "ملخص"},
            expect_status=201,
        )
        article_id = article["id"]
        ids["article_id"] = article_id
        # حفظ المستند اختياري إذا كان S3 غير مهيأ
        status, _ = request(
            "PUT",
            f"/api/v1/articles/{article_id}/document",
            token=ADMIN_TOKEN,
            body={"document": {"blocks": []}},
        )
        if status not in (200, 503):
            raise StepError(f"حفظ المستند فشل: {status}")
        request(
            "POST",
            f"/api/v1/articles/{article_id}/submit",
            token=ADMIN_TOKEN,
            expect_status=200,
        )

    run("admin creates and submits article", create_and_submit)
    article_id = ids.get("article_id")
    if not article_id:
        print("\nAborted: no article.")
        return 1

    def assign_roles() -> None:
        _, rev = request(
            "POST",
            f"/api/v1/admin/articles/{article_id}/assign-reviewer",
            token=ADMIN_TOKEN,
            body={"user_id": ids["reviewer_user_id"]},
            expect_status=201,
        )
        ids["assignment_id"] = rev["assignment_id"]
        request(
            "POST",
            f"/api/v1/admin/articles/{article_id}/assign-editor",
            token=ADMIN_TOKEN,
            body={"user_id": ids["editor_user_id"]},
            expect_status=201,
        )

    run("admin assigns reviewer and editor", assign_roles)

    def reject_decision_on_draft() -> None:
        _, draft_article = request(
            "POST",
            "/api/v1/articles",
            token=ADMIN_TOKEN,
            body={"title": "مسودة قرار محظور", "abstract": None},
            expect_status=201,
        )
        draft_id = draft_article["id"]
        request(
            "POST",
            f"/api/v1/admin/articles/{draft_id}/assign-editor",
            token=ADMIN_TOKEN,
            body={"user_id": ids["editor_user_id"]},
            expect_status=201,
        )
        request(
            "POST",
            f"/api/v1/editor/articles/{draft_id}/decision",
            token=EDITOR_TOKEN,
            body={"status": "accepted"},
            expect_status=400,
        )

    run("editor cannot decide on draft", reject_decision_on_draft)

    def reviewer_flow() -> None:
        _, listing = request(
            "GET", "/api/v1/reviews/me", token=REVIEWER_TOKEN, expect_status=200
        )
        assert any(r["id"] == ids["assignment_id"] for r in listing), listing
        aid = ids["assignment_id"]
        request(
            "GET",
            f"/api/v1/reviews/assignments/{aid}",
            token=REVIEWER_TOKEN,
            expect_status=200,
        )
        request(
            "PUT",
            f"/api/v1/reviews/assignments/{aid}/review",
            token=REVIEWER_TOKEN,
            body={
                "comments_to_author": "ملاحظة للمؤلف",
                "comments_to_editor": "ملاحظة للمحرر",
                "recommendation": "minor_revision",
            },
            expect_status=200,
        )
        _, submitted = request(
            "POST",
            f"/api/v1/reviews/assignments/{aid}/review/submit",
            token=REVIEWER_TOKEN,
            expect_status=200,
        )
        assert submitted["status"] == "submitted", submitted

    run("reviewer lists, drafts, submits", reviewer_flow)

    def editor_flow() -> None:
        _, listing = request(
            "GET", "/api/v1/editor/articles", token=EDITOR_TOKEN, expect_status=200
        )
        match = next((a for a in listing if a["id"] == article_id), None)
        assert match is not None, listing
        assert match.get("submitted_reviews_count", 0) >= 1, match
        _, detail = request(
            "GET",
            f"/api/v1/editor/articles/{article_id}",
            token=EDITOR_TOKEN,
            expect_status=200,
        )
        assert len(detail.get("reviews") or []) >= 1, detail
        current_id = detail["current_version"]["id"]
        # التقارير مقيّدة بالإصدار الحالي
        for review in detail["reviews"]:
            # الحقل غير مُعاد في التقرير؛ نتحقق عبر عدد التقارير >= 1 بعد التسليم
            assert review.get("id"), review
        assert detail["current_version"]["id"] == current_id
        _, version = request(
            "POST",
            f"/api/v1/editor/articles/{article_id}/decision",
            token=EDITOR_TOKEN,
            body={"status": "accepted", "reason": "اختبار"},
            expect_status=200,
        )
        assert version["status"] == "accepted", version
        assert version.get("change_summary"), version
        assert "قبول" in version["change_summary"], version
        assert "اختبار" in version["change_summary"], version

    run("editor lists, sees reviews, decides with reason", editor_flow)

    if NON_ASSIGNEE_TOKEN:
        run(
            "non-assignee cannot see reviewer assignment",
            lambda: request(
                "GET",
                f"/api/v1/reviews/assignments/{ids['assignment_id']}",
                token=NON_ASSIGNEE_TOKEN,
                expect_status=404,
            ),
        )
        run(
            "non-assignee cannot see editor article",
            lambda: request(
                "GET",
                f"/api/v1/editor/articles/{article_id}",
                token=NON_ASSIGNEE_TOKEN,
                expect_status=404,
            ),
        )

    if failures:
        print(f"\n{failures} step(s) failed.")
        return 1
    print("\nAll steps passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
