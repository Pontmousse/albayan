# Notifications and Issues Spec

## Purpose

Add two logged-in product systems to Al-Bayan:

- **Notifications:** user-targeted alerts for system events, mentions, issue replies, issue upvotes, and future activity types.
- **Issues:** user feedback/reporting board with categories, status tracking, upvotes, optional images, admin moderation, and notifications for relevant activity.

This spec is organized into four implementation phases. Each phase includes backend and frontend work for both systems so the feature can ship incrementally without blocking unrelated areas.

## Global Rules

- All user-facing dates in the frontend must use the shared date helpers in `frontend/src/lib/format-date.ts`. Add a relative Arabic timestamp helper there rather than formatting dates inside components.
- Store timestamps and API payloads as Gregorian ISO strings.
- These systems are logged-in only. API endpoints require the authenticated current user unless explicitly marked public in a later spec.
- Admin-only operations use the existing role/admin capability model. Regular users can view, create, and upvote issues, but cannot change issue status.
- Do not store database logic, secrets, S3 credentials, or privileged moderation decisions in `frontend/`.
- Issue image uploads allow at most three images per issue. Enforce this in application logic, even if storage limits are also added later.
- Notification metadata is flexible JSON, but API responses should expose only metadata needed by the current UI.

## Data Model

### `notifications`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK -> `users.id` | Recipient |
| `actor_id` | UUID FK -> `users.id`, nullable | User who triggered the notification |
| `type` | enum/string | `system`, `mention`, `issue_reply`, `issue_upvoted`, etc. |
| `title` | string | Short Arabic-friendly notification title |
| `body` | text | Optional display body |
| `link` | string, nullable | Relative app path preferred |
| `metadata` | JSONB | Per-type payload |
| `is_read` | boolean | Default `false` |
| `read_at` | timestamptz, nullable | Set when read |
| `created_at` | timestamptz | |

Indexes:

- `(user_id, created_at DESC)`
- `(user_id, is_read)`

### `issues`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK -> `users.id` | Reporter |
| `title` | string | Required |
| `description` | text | Required |
| `status` | enum/string | `open`, `in_progress`, `resolved`, `closed`; admin-editable |
| `category` | enum/string | `bug`, `feature_request`, `feedback`; user-selected on submit |
| `upvote_count` | integer | Denormalized counter, default `0` |
| `created_at` | timestamptz | |
| `updated_at` | timestamptz | |

Recommended indexes:

- `(status, created_at DESC)`
- `(category, created_at DESC)`
- `(upvote_count DESC, created_at DESC)`
- `(user_id, created_at DESC)`

### `issue_upvotes`

| Column | Type | Notes |
|---|---|---|
| `issue_id` | UUID FK -> `issues.id` | Part of unique key |
| `user_id` | UUID FK -> `users.id` | Part of unique key |
| `created_at` | timestamptz | |

Constraints:

- Unique `(issue_id, user_id)`

### `issue_images`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `issue_id` | UUID FK -> `issues.id` | |
| `s3_key` | string | Storage object key |
| `position` | integer | Display order |

Recommended constraints:

- Unique `(issue_id, position)`
- App-layer max of three rows per issue

## API Shape

### Notifications

| Method | Path | Access | Purpose |
|---|---|---|---|
| `GET` | `/notifications?limit=10` | current user | Latest notifications for bell dropdown |
| `GET` | `/notifications?limit=&cursor=` | current user | Paginated notification center |
| `GET` | `/notifications/unread-count` | current user | Badge count |
| `PATCH` | `/notifications/{id}/read` | recipient only | Mark one notification read |
| `PATCH` | `/notifications/read-all` | current user | Mark all read |

Notification response fields:

```json
{
  "id": "uuid",
  "type": "issue_upvoted",
  "title": "صوّت مستخدم على بلاغك",
  "body": "حصل البلاغ على تصويت جديد.",
  "link": "/maktabi/issues/...",
  "is_read": false,
  "read_at": null,
  "created_at": "2026-08-28T12:00:00Z",
  "actor": {
    "id": "uuid",
    "full_name": "..."
  },
  "metadata": {
    "issue_id": "uuid"
  }
}
```

### Issues

| Method | Path | Access | Purpose |
|---|---|---|---|
| `GET` | `/issues` | current user | List visible issues |
| `POST` | `/issues` | current user | Create issue, subject to rate limit |
| `GET` | `/issues/{id}` | current user | Detail view |
| `POST` | `/issues/{id}/upvote` | current user | Add current user's upvote |
| `DELETE` | `/issues/{id}/upvote` | current user | Remove current user's upvote |
| `PATCH` | `/issues/{id}/status` | admin | Change status |
| `GET` | `/admin/issues` | admin | Filterable/sortable admin list |

Issue list filters:

- `status=open|in_progress|resolved|closed`
- `category=bug|feature_request|feedback`
- `sort=date|upvotes`
- `direction=asc|desc`
- pagination with `limit` and `cursor` or existing local pattern

Issue response fields should include:

- `id`, `title`, `description`, `status`, `category`
- `user_id` and reporter display summary
- `upvote_count`
- `current_user_upvoted`
- ordered image metadata
- `created_at`, `updated_at`

## Rate Limiting

Before creating a new issue, check:

```sql
count(*) where user_id = :current_user_id and created_at > now() - interval '24 hours'
```

Initial limit: **5 issues per user per 24 hours**.

Return `429` with a localized, user-safe error message when exceeded. Admins may either share the same limit or bypass it; choose one policy before implementation and document it in code.

## Phase 1: Backend Foundations

### Notifications Backend

- Add notification model, enum/type constants, migration, indexes, and schemas.
- Add an internal notification creation service:
  - accepts `user_id`, `type`, `title`, `body`, `link`, `actor_id`, `metadata`
  - prevents self-notification where product logic says it is noisy, such as a user upvoting their own issue if self-upvotes are later allowed
  - keeps metadata serializable and minimal
- Add current-user endpoints:
  - latest notifications
  - unread count
  - mark one as read
  - mark all as read
- Authorization requirement: a user can only read or mutate their own notifications.

### Notifications Frontend

- Add typed API client calls for latest notifications, unread count, mark read, and mark all read.
- Add a relative Arabic timestamp helper in `frontend/src/lib/format-date.ts`.
- Do not add global UI yet beyond any minimal integration needed to test API wiring.

### Issues Backend

- Add issue, issue upvote, and issue image models, enums/type constants, migrations, indexes, and schemas.
- Add create/list/detail endpoints for logged-in users.
- Enforce:
  - required title, description, and category
  - category is user-selected
  - default status is `open`
  - app-layer max three images
  - 24-hour per-user issue creation limit
- Include `current_user_upvoted` in issue responses.

### Issues Frontend

- Add typed API client calls for list, detail, and create.
- Add route shell or placeholder entry point for the user-facing issues area, gated to logged-in users.
- Keep visual work minimal until Phase 2.

### Phase 1 Acceptance

- Migrations apply cleanly.
- Logged-in user can create an issue through API.
- Logged-in user can fetch own notifications and unread count.
- Unauthorized users receive auth errors.
- A user cannot read or mark another user's notification.

## Phase 2: User-Facing Experience

### Notifications Backend

- Add notification events from issue actions:
  - notify issue reporter when another user upvotes the issue
  - prepare event type for `issue_reply`, even if replies are implemented later
- Ensure notification links point to stable issue detail routes.
- Return latest notifications ordered by `created_at DESC`, default limit `10`.

### Notifications Frontend

- Add bell button in logged-in app chrome only.
- Show unread badge; hide or soften badge when count is zero.
- Build RTL Arabic dropdown:
  - latest about 10 notifications
  - unread notifications visually distinct
  - Arabic relative timestamps
  - "mark all as read" action
  - "see all" link
  - empty state
- Mark notification as read when the user opens/clicks an item, using optimistic UI where appropriate.

### Issues Backend

- Add upvote and remove-upvote endpoints.
- Enforce unique `(issue_id, user_id)` at the database level and handle conflicts gracefully.
- Update `issues.upvote_count` transactionally when votes change.
- Prevent count drift with transaction-safe increments/decrements.

### Issues Frontend

- Build logged-in user issue list:
  - status and category display
  - upvote count
  - current user's upvote state
  - sort by date or upvotes
  - filter by status and category
- Build create issue form:
  - category selector: bug, feature request, feedback
  - title and description fields
  - up to three images if upload infrastructure is ready; otherwise keep the image control hidden until Phase 4
- Build issue detail view with status, images, reporter summary, and upvote control.

### Phase 2 Acceptance

- Bell dropdown appears only for logged-in users.
- Unread badge updates after mark-read and mark-all-read.
- A user can create, view, and upvote an issue.
- Duplicate upvote attempts do not create duplicate rows or inflate the count.
- Issue reporter receives a notification when another user upvotes their issue.

## Phase 3: Admin Workflow

### Notifications Backend

- Add admin/system notification helper for status changes:
  - when an admin changes issue status, notify the reporter
  - include previous and next status in metadata
- Add test coverage for notification creation on issue status updates.

### Notifications Frontend

- Add notification copy and visual treatment for issue status changes.
- Ensure issue status notification links open the correct issue detail page.
- Consider refreshing unread count after admin-triggered status updates when the user returns to the app.

### Issues Backend

- Add admin-only `PATCH /issues/{id}/status`.
- Add admin list endpoint with filters/sorting:
  - status
  - category
  - upvotes
  - date
- Validate status transitions at minimum by accepted enum values. Add stricter transition rules only if editorial policy requires them.
- Ensure non-admin status patch attempts return forbidden.

### Issues Frontend

- Add admin-facing issue list view:
  - all issues
  - filterable and sortable by status, category, upvotes, and date
  - status edit control
  - visible reporter and created date
- In regular user views, show live/latest status but do not render status editing controls.
- Add optimistic or refetch-based status update behavior for admins.

### Phase 3 Acceptance

- Admins can filter/sort all issues.
- Admins can change status.
- Regular users cannot access status mutation, even by direct API request.
- Reporter receives a notification when status changes.
- Regular user issue detail reflects the updated status after refresh or polling.

## Phase 4: Polish, Images, and Reliability

### Notifications Backend

- Add pagination support for a full notification center if not completed earlier.
- Add retention and cleanup policy only if product requires it; otherwise keep all notification rows.
- Add structured tests for:
  - unread count
  - mark all read
  - recipient isolation
  - issue-generated notifications
- Add idempotency safeguards for noisy events where repeated actions may occur.

### Notifications Frontend

- Build full "see all" notifications page.
- Add loading, error, and empty states.
- Tune dropdown keyboard behavior:
  - escape closes
  - focus returns to bell
  - links are reachable by keyboard
- Ensure the dropdown works in RTL at mobile and desktop widths without clipped text.

### Issues Backend

- Complete issue image upload flow:
  - generate or accept S3 keys through the existing backend-owned storage pattern
  - enforce max three images
  - preserve image order with `position`
  - delete or detach orphaned uploads if issue creation fails
- Add tests for:
  - rate limit
  - duplicate upvotes
  - upvote count consistency
  - admin-only status changes
  - image limit
- Add maintenance job or admin action to recalculate `upvote_count` from `issue_upvotes` if drift is ever detected.

### Issues Frontend

- Enable image attachment UI once backend upload flow exists:
  - max three images
  - preview thumbnails
  - remove/reorder before submit if feasible
  - upload errors shown inline
- Improve filtering/sorting controls for both user and admin lists.
- Add polished empty states:
  - no issues yet
  - no results for active filters
  - no notifications yet
- Verify Arabic labels, RTL alignment, responsive behavior, and visual distinction for unread/read states.

### Phase 4 Acceptance

- Users can submit issues with up to three images.
- The fourth image is blocked before or during submission with a clear error.
- Full notification center paginates correctly.
- Keyboard and mobile behavior are usable.
- Lint/build pass for frontend changes, and backend tests pass for the new feature area.

## Suggested Arabic UI Labels

Notifications:

- Bell tooltip: `الإشعارات`
- Mark all read: `تعيين الكل كمقروء`
- See all: `عرض الكل`
- Empty state: `لا توجد إشعارات بعد`

Issues:

- Main nav label: `البلاغات والمقترحات`
- Create issue: `إرسال بلاغ`
- Upvote: `تصويت`
- Already upvoted state: `صوّتَّ`
- Admin status action: `تحديث الحالة`

Statuses:

- `open`: `مفتوح`
- `in_progress`: `قيد المعالجة`
- `resolved`: `تم الحل`
- `closed`: `مغلق`

Categories:

- `bug`: `خلل`
- `feature_request`: `طلب ميزة`
- `feedback`: `ملاحظة`
