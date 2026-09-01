# Planned Transactional Emails

This package contains the shared Albayan email system. Implemented templates
reuse `AlbayanLayout` and stay aligned with the green, gold, ink, and paper
palette already used by the application.

| Email | Recipient | Trigger | Notes |
| --- | --- | --- | --- |
| Welcome | New user | First local backend user creation from Clerk auth | Implemented first. |
| Application invitation | Invited email | Admin creates an application invitation | Implemented with provider-owned URL/status, recipient name, and branded delivery. |
| Sign-up verification code | New user | Clerk `email.created` webhook for sign-up email verification | Implemented with Clerk-owned OTP validation and Resend delivery. |
| Password reset code | Existing user | Clerk `email.created` webhook for password recovery | Implemented with Clerk-owned OTP validation and Resend delivery. |
| Submission received | Corresponding author | Manuscript submission | Implemented as `submission-received-ar`. |
| New submission alert | Admins/editors | Manuscript submission | Implemented as `new-submission-alert-ar`. |
| Editor assigned | Editor | Admin assigns existing editor | Implemented as `editor-assigned-ar`. |
| Reviewer invitation | Invited reviewer email | Admin invites reviewer by email | Implemented as `review-invitation-ar`. |
| Reviewer assignment | Existing reviewer user | Admin assigns existing reviewer | Implemented as `reviewer-assigned-ar`. |
| Review reminder | Existing reviewer user | Midpoint and one day before review due date | Implemented as `review-reminder-ar`; called from scheduled service. |
| Review submitted | Assigned editors/admins | Reviewer submits review | Implemented as `review-submitted-ar`. |
| Under review / accepted / rejected | Corresponding author | Editorial decision | Implemented as `decision-ar`. |
| Published | Authors | Article status set to published | Implemented as `article-published-ar`. |
| Unread notification digest | Users with > 5 unread notifications | Weekly digest job | Implemented as `unread-notifications-digest-ar`. |
| Revision requested | Corresponding author | Future revision workflow | Add only after backend gains a revision status/workflow. |
| Revision received | Editors/admins | Future revision workflow | Add only after backend gains a revision status/workflow. |
| Account deletion request received | Requesting user | Deletion request submitted | Future courtesy template; current v1 shows in-app confirmation. |
| Account deletion request resolved | Requesting user | Admin resolves deletion request | Future template after policy wording is finalized. |

## Assets Needed

- Transparent Albayan logo, stacked and horizontal.
- Email-safe header arch artwork in green/gold/paper.
- Subtle geometric pattern tile.
- Gold divider/flourish image.
- Separate left and truly mirrored right footer-corner ornaments.
- Small feature icons for publish/read/community.
- Social/contact icons, if official links exist.
- Production HTTPS asset host path for email images.
