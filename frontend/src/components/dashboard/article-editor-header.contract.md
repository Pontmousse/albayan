# Focused article editor header contract

The article authoring route (`/maktabi/maqalati/[id]/tahrir`) deliberately does not render the normal journal `SiteHeader` or `SiteFooter`.

Its compact editor header owns Al Bayan host navigation while BuTeX owns document editing. The header must keep save/autosave state visible, expose article tools (assets, equation mappings, revision history, submission, and DEV JSON when enabled), and keep the author able to reach Maktabi, My Articles, notifications, account settings, and the normal journal destinations.

On small screens the secondary controls move into the existing `MobileSheet` pattern. On desktop they use a bounded dropdown. BuTeX equation editing may continue to take over the browser viewport temporarily.
