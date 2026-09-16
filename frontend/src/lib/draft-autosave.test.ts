import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "./api";
import { DraftAutosaveController } from "./draft-autosave";
import type { DraftRevision } from "./api/articles";

const document = (title: string) =>
  ({ node_type: "DocumentObject", meta: { title, abstract: "" }, blocks: [] }) as DraftRevision["document"];

const revision = (number: number, title: string): DraftRevision => ({
  revision_id: String(number),
  revision_number: number,
  document_hash: "a".repeat(64),
  actor_type: "human",
  reason: "autosave",
  created_at: "2026-09-15T12:00:00Z",
  restored_from_id: null,
  restored_from_revision_number: null,
  document: document(title),
});

afterEach(() => vi.useRealTimers());

describe("DraftAutosaveController", () => {
  it("debounces idle edits and enforces the continuous-edit maximum", async () => {
    vi.useFakeTimers();
    const save = vi.fn(async (_doc, base: number) => revision(base + 1, "saved"));
    const controller = new DraftAutosaveController({
      initial: revision(1, "a"), save, reload: vi.fn(), onState: vi.fn(), onConflict: vi.fn(),
    });
    controller.update(document("b"));
    await vi.advanceTimersByTimeAsync(1_499);
    expect(save).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(1);
    expect(save).toHaveBeenCalledTimes(1);

    for (let index = 0; index < 11; index += 1) {
      controller.update(document(`continuous-${index}`));
      await vi.advanceTimersByTimeAsync(1_400);
    }
    expect(save.mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  it("coalesces an edit made during an in-flight save", async () => {
    vi.useFakeTimers();
    let release!: (value: DraftRevision) => void;
    const first = new Promise<DraftRevision>((resolve) => { release = resolve; });
    const save = vi.fn().mockReturnValueOnce(first).mockResolvedValueOnce(revision(3, "c"));
    const controller = new DraftAutosaveController({
      initial: revision(1, "a"), save, reload: vi.fn(), onState: vi.fn(), onConflict: vi.fn(),
    });
    controller.update(document("b"));
    await vi.advanceTimersByTimeAsync(1_500);
    controller.update(document("c"));
    release(revision(2, "b"));
    await vi.runAllTimersAsync();
    await Promise.resolve();
    expect(save).toHaveBeenCalledTimes(2);
    expect(save.mock.calls[1][1]).toBe(2);
  });

  it("retries transient failures at 2, 5, and 15 seconds", async () => {
    vi.useFakeTimers();
    const save = vi.fn().mockRejectedValue(new ApiError("x", 503));
    const controller = new DraftAutosaveController({
      initial: revision(1, "a"), save, reload: vi.fn(), onState: vi.fn(), onConflict: vi.fn(),
    });
    controller.update(document("b"));
    await vi.advanceTimersByTimeAsync(1_500 + 2_000 + 5_000 + 15_000);
    expect(save).toHaveBeenCalledTimes(4);
  });

  it("reloads the server draft and reports a conflict", async () => {
    vi.useFakeTimers();
    const onConflict = vi.fn();
    const onState = vi.fn();
    const controller = new DraftAutosaveController({
      initial: revision(1, "a"),
      save: vi.fn().mockRejectedValue(new ApiError("conflict", 409)),
      reload: vi.fn().mockResolvedValue(revision(2, "agent")),
      onState,
      onConflict,
    });
    controller.update(document("local"));
    await vi.advanceTimersByTimeAsync(1_500);
    expect(onConflict).toHaveBeenCalledWith(revision(2, "agent"));
    expect(onState).toHaveBeenLastCalledWith(expect.objectContaining({ kind: "conflict" }));
    expect(controller.isUnsafeToLeave()).toBe(false);
  });

  it("adopts the canonical server document after normalization", async () => {
    vi.useFakeTimers();
    const onCanonical = vi.fn();
    const controller = new DraftAutosaveController({
      initial: revision(1, "a"),
      save: vi.fn().mockResolvedValue(revision(2, "canonical")),
      reload: vi.fn(),
      onState: vi.fn(),
      onConflict: vi.fn(),
      onCanonical,
    });
    controller.update(document("client"));
    await vi.advanceTimersByTimeAsync(1_500);
    expect(onCanonical).toHaveBeenCalledWith(revision(2, "canonical"));
    expect(controller.isUnsafeToLeave()).toBe(false);
    expect(controller.getBaseRevision()).toBe(2);
  });

  it("exposes the latest server base after conflict reload", async () => {
    vi.useFakeTimers();
    const controller = new DraftAutosaveController({
      initial: revision(3, "before"),
      save: vi.fn().mockRejectedValue(new ApiError("conflict", 409)),
      reload: vi.fn().mockResolvedValue(revision(8, "external")),
      onState: vi.fn(),
      onConflict: vi.fn(),
    });
    controller.update(document("local"));
    await vi.advanceTimersByTimeAsync(1_500);
    expect(controller.getBaseRevision()).toBe(8);
  });

  it("does not retry a validation failure", async () => {
    vi.useFakeTimers();
    const save = vi.fn().mockRejectedValue(new ApiError("invalid", 422));
    const controller = new DraftAutosaveController({
      initial: revision(1, "a"),
      save,
      reload: vi.fn(),
      onState: vi.fn(),
      onConflict: vi.fn(),
    });
    controller.update(document("invalid"));
    await vi.advanceTimersByTimeAsync(30_000);
    expect(save).toHaveBeenCalledTimes(1);
    expect(controller.isUnsafeToLeave()).toBe(true);
  });
});
