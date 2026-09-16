import { ApiError } from "./api";
import type { DraftRevision } from "./api/articles";
import type { Document2Json } from "@drghaliasri/butex/document2";

export type AutosaveState =
  | { kind: "saved"; dirty: false }
  | { kind: "pending"; dirty: true }
  | { kind: "saving"; dirty: true }
  | { kind: "failed"; dirty: true; message: string }
  | { kind: "conflict"; dirty: false; message: string };

type Options = {
  initial: DraftRevision;
  save: (document: Document2Json, baseRevision: number) => Promise<DraftRevision>;
  reload: () => Promise<DraftRevision>;
  onState: (state: AutosaveState) => void;
  onConflict: (latest: DraftRevision) => void;
  onCanonical?: (latest: DraftRevision) => void;
  idleMs?: number;
  maximumMs?: number;
  retryMs?: number[];
};

const CONFLICT_NOTICE =
  "وصلت تعديلات أحدث من مصدر آخر؛ حُمّلت أحدث مسودة وحُذفت التغييرات المحلية غير المحفوظة.";

export class DraftAutosaveController {
  private readonly options: Required<
    Pick<Options, "idleMs" | "maximumMs" | "retryMs">
  > &
    Omit<Options, "idleMs" | "maximumMs" | "retryMs">;
  private baseRevision: number;
  private cleanSnapshot: string;
  private latestSnapshot: string;
  private latestDocument: Document2Json;
  private inFlight: Promise<boolean> | null = null;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private maximumTimer: ReturnType<typeof setTimeout> | null = null;
  private retryTimer: ReturnType<typeof setTimeout> | null = null;
  private retryIndex = 0;
  private failed = false;
  private disposed = false;

  constructor(options: Options) {
    this.options = {
      ...options,
      idleMs: options.idleMs ?? 1_500,
      maximumMs: options.maximumMs ?? 15_000,
      retryMs: options.retryMs ?? [2_000, 5_000, 15_000],
    };
    this.baseRevision = options.initial.revision_number;
    this.latestDocument = options.initial.document;
    this.cleanSnapshot = JSON.stringify(options.initial.document);
    this.latestSnapshot = this.cleanSnapshot;
    options.onState({ kind: "saved", dirty: false });
  }

  update(document: Document2Json): void {
    if (this.disposed) return;
    this.latestDocument = document;
    this.latestSnapshot = JSON.stringify(document);
    if (!this.inFlight && this.latestSnapshot === this.cleanSnapshot) {
      this.cancelScheduled();
      this.failed = false;
      this.options.onState({ kind: "saved", dirty: false });
      return;
    }
    this.failed = false;
    this.options.onState({ kind: "pending", dirty: true });
    if (this.inFlight) return;
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => void this.saveNewest(), this.options.idleMs);
    if (!this.maximumTimer) {
      this.maximumTimer = setTimeout(
        () => void this.saveNewest(),
        this.options.maximumMs,
      );
    }
  }

  isUnsafeToLeave(): boolean {
    return (
      this.inFlight !== null ||
      this.failed ||
      this.latestSnapshot !== this.cleanSnapshot
    );
  }

  getBaseRevision(): number {
    return this.baseRevision;
  }

  async flush(): Promise<boolean> {
    this.cancelScheduled();
    if (this.inFlight) await this.inFlight;
    if (this.latestSnapshot === this.cleanSnapshot && !this.failed) return true;
    this.retryIndex = 0;
    return this.saveNewest(false);
  }

  dispose(): void {
    this.disposed = true;
    this.cancelScheduled();
  }

  private cancelScheduled(): void {
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    if (this.maximumTimer) clearTimeout(this.maximumTimer);
    if (this.retryTimer) clearTimeout(this.retryTimer);
    this.debounceTimer = null;
    this.maximumTimer = null;
    this.retryTimer = null;
  }

  private isTransient(error: unknown): boolean {
    return !(error instanceof ApiError) || error.status === 429 || error.status >= 500;
  }

  private async handleConflict(): Promise<boolean> {
    this.cancelScheduled();
    try {
      const latest = await this.options.reload();
      this.baseRevision = latest.revision_number;
      this.latestDocument = latest.document;
      this.latestSnapshot = JSON.stringify(latest.document);
      this.cleanSnapshot = this.latestSnapshot;
      this.failed = false;
      this.retryIndex = 0;
      this.options.onConflict(latest);
      this.options.onState({
        kind: "conflict",
        dirty: false,
        message: CONFLICT_NOTICE,
      });
      return false;
    } catch {
      this.failed = true;
      this.options.onState({
        kind: "failed",
        dirty: true,
        message: "تعذّر تحميل أحدث مسودة بعد تعارض التعديلات.",
      });
      return false;
    }
  }

  private saveNewest(scheduleRetry = true): Promise<boolean> {
    if (this.inFlight) return this.inFlight;
    this.cancelScheduled();
    const document = this.latestDocument;
    const snapshot = this.latestSnapshot;
    const baseRevision = this.baseRevision;
    this.options.onState({ kind: "saving", dirty: true });

    const operation = this.options
      .save(document, baseRevision)
      .then((saved) => {
        const canonicalSnapshot = JSON.stringify(saved.document);
        this.baseRevision = saved.revision_number;
        this.cleanSnapshot = canonicalSnapshot;
        this.failed = false;
        this.retryIndex = 0;
        if (this.latestSnapshot !== snapshot) {
          this.options.onState({ kind: "pending", dirty: true });
        } else {
          this.latestDocument = saved.document;
          this.latestSnapshot = canonicalSnapshot;
          if (canonicalSnapshot !== snapshot) this.options.onCanonical?.(saved);
          this.options.onState({ kind: "saved", dirty: false });
        }
        return true;
      })
      .catch(async (error: unknown) => {
        if (error instanceof ApiError && error.status === 409) {
          return this.handleConflict();
        }
        const transient = this.isTransient(error);
        this.failed = true;
        this.options.onState({
          kind: "failed",
          dirty: true,
          message: transient
            ? "تعذّر الحفظ التلقائي. سنعيد المحاولة مع الاحتفاظ بتعديلاتك."
            : "تعذّر حفظ التعديلات. راجع محتوى المقال ثم حاول مجدداً.",
        });
        if (
          scheduleRetry &&
          transient &&
          this.retryIndex < this.options.retryMs.length
        ) {
          const delay = this.options.retryMs[this.retryIndex++];
          this.retryTimer = setTimeout(() => void this.saveNewest(), delay);
        }
        return false;
      })
      .finally(() => {
        this.inFlight = null;
        if (!this.failed && this.latestSnapshot !== this.cleanSnapshot) {
          queueMicrotask(() => void this.saveNewest());
        }
      });
    this.inFlight = operation;
    return operation;
  }
}
