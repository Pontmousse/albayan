import type {
  DraftRevision,
  DraftRevisionHistoryDetail,
  DraftRevisionHistoryItem,
} from "./api/articles";

export type HistorySaveStatus =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "failed"; message: string };

export type HistoryFlushController = {
  isUnsafeToLeave: () => boolean;
  flush: () => Promise<boolean>;
};

export function historyItemFromLocalRevision(
  revision: DraftRevision,
): DraftRevisionHistoryItem {
  return {
    revision_id: revision.revision_id,
    revision_number: revision.revision_number,
    document_hash: revision.document_hash,
    actor_type: revision.actor_type,
    reason: revision.reason,
    created_at: revision.created_at,
    created_by: null,
    created_by_name: null,
    restored_from_id: revision.restored_from_id,
    restored_from_revision_number: revision.restored_from_revision_number,
    is_current: true,
  };
}

export function historyDetailFromLocalRevision(
  revision: DraftRevision,
  metadata?: DraftRevisionHistoryItem | null,
): DraftRevisionHistoryDetail {
  return {
    ...historyItemFromLocalRevision(revision),
    ...metadata,
    revision_id: revision.revision_id,
    revision_number: revision.revision_number,
    document_hash: revision.document_hash,
    actor_type: revision.actor_type,
    reason: revision.reason,
    created_at: revision.created_at,
    restored_from_id: revision.restored_from_id,
    restored_from_revision_number: revision.restored_from_revision_number,
    is_current: metadata?.is_current ?? true,
    document: revision.document,
  };
}

export function findLocalHistoryDetail(
  revisionId: string,
  localDetails: ReadonlyMap<string, DraftRevisionHistoryDetail>,
): DraftRevisionHistoryDetail | null {
  return localDetails.get(revisionId) ?? null;
}

export function openHistoryWithBackgroundFlush({
  controller,
  onOpen,
  onStatus,
}: {
  controller: HistoryFlushController | null;
  onOpen: () => void;
  onStatus: (status: HistorySaveStatus) => void;
}): void {
  onOpen();

  if (!controller) {
    onStatus({
      kind: "failed",
      message: "تعذّر تهيئة الحفظ التلقائي، لكن يمكنك تصفح النسخ المحفوظة.",
    });
    return;
  }

  if (!controller.isUnsafeToLeave()) {
    onStatus({ kind: "idle" });
    return;
  }

  onStatus({ kind: "saving" });
  void controller
    .flush()
    .then((saved) => {
      if (saved || !controller.isUnsafeToLeave()) {
        onStatus({ kind: "idle" });
        return;
      }
      onStatus({
        kind: "failed",
        message:
          "تعذّر حفظ أحدث تغييرات جلسة التحرير. يمكنك متابعة تصفح النسخ المحفوظة، ولن تظهر التغييرات غير المحفوظة كنسخة تاريخية.",
      });
    })
    .catch(() => {
      onStatus({
        kind: "failed",
        message:
          "تعذّر حفظ أحدث تغييرات جلسة التحرير. يمكنك متابعة تصفح النسخ المحفوظة، ولن تظهر التغييرات غير المحفوظة كنسخة تاريخية.",
      });
    });
}
