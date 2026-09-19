import { afterEach, describe, expect, it, vi } from "vitest";
import { getDraftRevisionChangeSummary } from "./revision-change-summary";

const getToken = vi.fn(async () => "token");

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe("revision change summary API", () => {
  it("requests the dedicated authenticated summary endpoint", async () => {
    const payload = {
      summary: {
        version: 1,
        items: [{ kind: "edited", text: "عُدّل عنوان المقال." }],
      },
    };
    const fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetch);

    await expect(
      getDraftRevisionChangeSummary(getToken, "article-1", "revision-2"),
    ).resolves.toEqual(payload);

    expect(fetch).toHaveBeenCalledOnce();
    expect(fetch.mock.calls[0][0]).toBe(
      "http://localhost:8000/api/v1/articles/article-1/draft/revisions/revision-2/change-summary",
    );
  });

  it("accepts summary null as the normal unavailable state", async () => {
    const fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ summary: null }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetch);

    await expect(
      getDraftRevisionChangeSummary(getToken, "article-1", "revision-1"),
    ).resolves.toEqual({ summary: null });
  });
});
