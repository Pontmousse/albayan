import { describe, expect, it } from "vitest";
import { isButexDocumentValid } from "./butex-validation";

const emptyDocument = {
  node_type: "DocumentObject",
  blocks: [],
};

describe("isButexDocumentValid", () => {
  it("accepts a structurally valid document", () => {
    expect(isButexDocumentValid(emptyDocument)).toBe(true);
  });

  it("rejects an image block without a selected image", () => {
    expect(
      isButexDocumentValid({
        ...emptyDocument,
        blocks: [{ command: "\\includegraphics", value: "   " }],
      }),
    ).toBe(false);
  });

  it("accepts image blocks backed by an asset id", () => {
    expect(
      isButexDocumentValid({
        ...emptyDocument,
        blocks: [
          {
            command: "\\includegraphics",
            value: "",
            asset_id: "assets/figure.png",
          },
        ],
      }),
    ).toBe(true);
  });

  it("rejects an empty nested image block", () => {
    expect(
      isButexDocumentValid({
        ...emptyDocument,
        blocks: [
          {
            command: "\\begin{itemize}",
            items: [{ value: "عنصر", blocks: [{ command: "\\includegraphics" }] }],
          },
        ],
      }),
    ).toBe(false);
  });

  it("rejects malformed input without throwing", () => {
    expect(isButexDocumentValid({ blocks: "invalid" })).toBe(false);
  });
});
