# Planned Transactional Emails

This package starts with the shared Albayan email system and the welcome email.
Future templates should reuse `AlbayanLayout` and stay aligned with the green,
gold, ink, and paper palette already used by the application.

| Email | Recipient | Trigger | Notes |
| --- | --- | --- | --- |
| Welcome | New user | First local backend user creation from Clerk auth | Implemented first. |
| Submission received | Corresponding author | Manuscript submission | Include title, version, and manuscript link. |
| New submission alert | Admins/editors | Manuscript submission | Route to admin/editor dashboard. |
| Editor assigned | Editor | Admin assigns existing editor | Include article title and editor URL. |
| Reviewer invitation | Invited reviewer email | Admin invites reviewer by email | Replaces current simple invitation later. |
| Reviewer assignment | Existing reviewer user | Admin assigns existing reviewer | Include review workspace URL. |
| Review submitted | Assigned editors/admins | Reviewer submits review | Include article title and report link. |
| Under review | Corresponding author | Editorial status set to under review | Keep tone concise and reassuring. |
| Accepted/rejected | Corresponding author | Editorial decision | Include decision and next action if any. |
| Published | Authors | Article status set to published | Include public article URL. |
| Revision requested | Corresponding author | Future revision workflow | Add only after backend gains a revision status/workflow. |

## Assets Needed

- Transparent Albayan logo, stacked and horizontal.
- Email-safe header arch artwork in green/gold/paper.
- Subtle geometric pattern tile.
- Gold divider/flourish image.
- Footer corner ornament.
- Small feature icons for publish/read/community.
- Social/contact icons, if official links exist.
- Production HTTPS asset host path for email images.
