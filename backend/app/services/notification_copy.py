from app.models.enums import IssueStatus

ISSUE_STATUS_LABELS = {
    IssueStatus.OPEN: "مفتوح",
    IssueStatus.IN_PROGRESS: "قيد المعالجة",
    IssueStatus.RESOLVED: "تم الحل",
    IssueStatus.CLOSED: "مغلق",
}


def issue_status_changed_title(next_status: IssueStatus) -> str:
    return f"تغيّرت حالة بلاغك إلى: {ISSUE_STATUS_LABELS[next_status]}"


def issue_status_changed_body(issue_title: str, next_status: IssueStatus) -> str:
    return f"تم تحديث حالة البلاغ «{issue_title}» إلى {ISSUE_STATUS_LABELS[next_status]}."
