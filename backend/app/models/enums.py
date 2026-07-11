import enum


class VersionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PUBLISHED = "published"


# Deprecated alias — status lives on article_versions, not articles
ArticleStatus = VersionStatus


class ReviewerAssignmentStatus(str, enum.Enum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"


class SourceType(str, enum.Enum):
    ZIP_UPLOAD = "zip_upload"
    WEB_EDITOR = "web_editor"


class CompileStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class ReviewRecommendation(str, enum.Enum):
    ACCEPT = "accept"
    MINOR_REVISION = "minor_revision"
    MAJOR_REVISION = "major_revision"
    REJECT = "reject"


class ReviewStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"


class InvitationRole(str, enum.Enum):
    REVIEWER = "reviewer"
    EDITOR = "editor"


class InvitationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
