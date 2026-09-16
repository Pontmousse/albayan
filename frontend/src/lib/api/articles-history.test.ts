import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getDraftRevision,
  listDraftRevisions,
  restoreDraftRevision,
} from "./articles";

const getToken = vi.fn(async () => "token");

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe("draft history API", () => {
  it("loads the retained list and a snapshot lazily", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ revision_id: "revision-1" }), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetch);

    await listDraftRevisions(getToken, "article-1");
    expect(fetch.mock.calls[0][0]).toBe(
      "http://localhost:8000/api/v1/articles/article-1/draft/revisions",
    );
    await getDraftRevision(getToken, "article-1", "revision-1");
    expect(fetch.mock.calls[1][0]).toBe(
      "http://localhost:8000/api/v1/articles/article-1/draft/revisions/revision-1",
    );
  });

  it("restores with the exact current base revision", async () => {
    const fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ revision_id: "revision-3" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetch);

    await restoreDraftRevision(
      getToken,
      "article-1",
      "revision-1",
      2,
    );
    expect(fetch).toHaveBeenCalledOnce();
    const [url, request] = fetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(
      "http://localhost:8000/api/v1/articles/article-1/draft/revisions/revision-1/restore",
    );
    expect(request.method).toBe("POST");
    expect(JSON.parse(String(request.body))).toEqual({ base_revision: 2 });
  });
});
