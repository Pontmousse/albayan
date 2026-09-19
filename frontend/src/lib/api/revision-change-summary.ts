import { apiFetch } from "@/lib/api";

export type RevisionChangeKind =
  | "added"
  | "removed"
  | "edited"
  | "moved"
  | "metadata"
  | "other";

export type RevisionChangeSummaryItem = {
  kind: RevisionChangeKind;
  text: string;
};

export type RevisionChangeSummaryV1 = {
  version: 1;
  items: RevisionChangeSummaryItem[];
};

export type DraftRevisionChangeSummaryResponse = {
  summary: RevisionChangeSummaryV1 | null;
};

type GetToken = () => Promise<string | null>;

export function getDraftRevisionChangeSummary(
  getToken: GetToken,
  articleId: string,
  revisionId: string,
) {
  return apiFetch<DraftRevisionChangeSummaryResponse>(
    `/api/v1/articles/${articleId}/draft/revisions/${revisionId}/change-summary`,
    getToken,
  );
}
