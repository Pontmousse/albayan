import { describe, expect, it, vi } from "vitest";
import type { DraftRevision } from "./api/articles";
import {
  findLocalHistoryDetail,
  historyDetailFromLocalRevision,
  openHistoryWithBackgroundFlush,
  type HistorySaveStatus,
} from "./draft-history-performance";

const document = (title: string) =>
  ({ node_type: "DocumentObject", meta: { title, abstract: "" }, blocks: [] }) as unknown as DraftRevision["document"];

const revision = (number: number, title: string): DraftRevision => ({
  revision_id: `rev-${number}`,
  revision_number: number,
  document_hash: "a".repeat(64),
  actor_type: "human",
  reason: "autosave",
  created_at: "2026-09-18T12:00:00Z",
  restored_from_id: null,
  restored_from_revision_number: null,
  document: document(title),
});

describe("draft history performance helpers", () => {
  it("opens synchronously before an unsafe draft finishes flushing", async () => {
    let resolveFlush!: (value: boolean) => void;
    const flush = vi.fn(() => new Promise<boolean>((resolve) => { resolveFlush = resolve; }));
    const events: string[] = [];
    const statuses: HistorySaveStatus[] = [];
    const controller = {
      isUnsafeToLeave: vi.fn(() => true),
      flush,
    };

    openHistoryWithBackgroundFlush({
      controller,
      onOpen: () => events.push("open"),
      onStatus: (status) => {
        statuses.push(status);
        events.push(status.kind);
      },
    });

    expect(events.slice(0, 2)).toEqual(["open", "saving"]);
    expect(flush).toHaveBeenCalledTimes(1);

    controller.isUnsafeToLeave.mockReturnValue(false);
    resolveFlush(true);
    await Promise.resolve();
    expect(statuses.at(-1)).toEqual({ kind: "idle" });
  });

  it("keeps history usable and reports a failed background save", async () => {
    const statuses: HistorySaveStatus[] = [];
    const controller = {
      isUnsafeToLeave: vi.fn(() => true),
      flush: vi.fn().mockResolvedValue(false),
    };

    openHistoryWithBackgroundFlush({
      controller,
      onOpen: vi.fn(),
      onStatus: (status) => statuses.push(status),
    });
    await Promise.resolve();

    expect(statuses[0]).toEqual({ kind: "saving" });
    expect(statuses.at(-1)?.kind).toBe("failed");
  });

  it("does not flush a clean draft when opening history", () => {
    const flush = vi.fn();
    const onOpen = vi.fn();
    const onStatus = vi.fn();

    openHistoryWithBackgroundFlush({
      controller: { isUnsafeToLeave: () => false, flush },
      onOpen,
      onStatus,
    });

    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(flush).not.toHaveBeenCalled();
    expect(onStatus).toHaveBeenLastCalledWith({ kind: "idle" });
  });

  it("reuses a locally available current revision document", () => {
    const current = revision(7, "current");
    const detail = historyDetailFromLocalRevision(current);
    const local = new Map([[current.revision_id, detail]]);

    expect(findLocalHistoryDetail(current.revision_id, local)).toBe(detail);
    expect(findLocalHistoryDetail("older", local)).toBeNull();
    expect(detail.document.meta?.title).toBe("current");
  });
});
