# ChatGPT MCP file transport findings

## Scope

This document records the completed investigation into how ChatGPT surfaces non-text MCP tool content for Al-Bayan. It covers the isolated `test_mcp_content_transport` probe, a real PDF retrieval, the native `openai/fileParams` JPEG upload path, and the application upload-to-storage-to-retrieval round trip.

The investigation is intentionally paused after these observations. No production transport representation is changed by this documentation.

## 1. Tool discovery is cached per existing conversation

PR #95 was merged and deployed successfully. The deployed service registered `test_mcp_content_transport` with `enable_transport_probe=True`, and Railway logs showed the OpenAI MCP client reconnecting successfully with HTTP 200.

However, the already-open ChatGPT conversation did not refresh its developer-MCP tool schema after the deployment. The newly deployed probe was therefore not callable from that conversation.

| Item | Observation |
| --- | --- |
| Service deployment | Successful |
| MCP reconnection after deployment | Successful |
| Probe registration | Successful |
| Discovery in the already-open chat | Not refreshed |
| Immediate conclusion | The initial blocked cases were a client-side discovery-cache limitation, not a server failure |

A fresh tool-discovery context is required before treating a newly deployed MCP tool as unavailable.

## 2. Isolated content-transport probe

The probe deliberately avoids FastAPI, object storage, Butex, and PDF compilation. It returns deterministic inline fixtures, so each case tests the ChatGPT/MCP content boundary itself.

| Case | Content class exercised | Purpose |
| --- | --- | --- |
| `image_content` | `ImageContent(image/png)` | Image-only MCP result, matching article-asset transport |
| `image_content_with_text` | Text + `ImageContent` | Whether companion text affects visibility |
| `embedded_text` | `EmbeddedResource(TextResourceContents)` | Embedded text-resource handling |
| `embedded_binary` | `EmbeddedResource(BlobResourceContents)`, octet-stream | Generic binary-resource handling |
| `embedded_png` | Blob resource, `image/png` | Image blob-resource handling |
| `embedded_pdf` | Blob resource, `application/pdf` | Same transport class used by article-PDF retrieval |
| `embedded_pdf_with_text` | Text + PDF blob resource | Whether companion text affects PDF/resource handling |
| `upload_file_params` | Sanitized text summary | Shape passed by ChatGPT through native `openai/fileParams` |

The probe remains useful for future client-regression checks, but it does not justify a transport change by itself.

## 3. Real PDF retrieval

A real article-PDF retrieval was tested separately from the deterministic PDF probe. The PDF flow confirmed that the application can compile and return an article PDF; the earlier inability to surface a file in a particular conversation cannot be attributed solely to compilation, FastAPI, object storage, or Butex.

This distinction matters: a successful backend result and a visible, persistent ChatGPT attachment are separate behaviors.

## 4. Native JPEG upload through `openai/fileParams`

A JPEG attached from the native client reached the MCP tool through `openai/fileParams`. The probe reports only sanitized structural information and deliberately does not download, expose, or persist signed download URLs or file IDs.

This established that the native upload parameter reaches the server. It does not make ChatGPT-provided media a durable application asset automatically.

## 5. Application upload, storage, and retrieval

The end-to-end application path was also validated:

1. The uploaded media was accepted by the application.
2. The application stored it successfully.
3. The stored asset was retrievable afterward.

The application-owned upload and storage path is therefore the correct durable path for article media.

## 6. Transient media behavior

Media supplied by ChatGPT/MCP can be transient from the conversation interface's perspective: an item may be present for a turn yet not remain available or render consistently later. This behavior is distinct from successful application storage and retrieval.

Consequently, ChatGPT/MCP media should not be treated as durable article storage. Durable article assets must continue to use the application's explicit upload and storage workflow.

## Conclusion and status

The investigation is paused. The evidence supports the following conclusions:

- Existing ChatGPT conversations can cache MCP tool discovery after a redeploy.
- The isolated probe separates content-transport behavior from the Al-Bayan backend and compiler.
- Native `openai/fileParams` reaches the MCP tool, but is not a persistence mechanism.
- The application upload → storage → retrieval path works and is the durable asset path.
- Transient or disappearing UI media does not establish a backend storage failure.

No further MCP transport changes are proposed at this time. Keep the probe feature-gated and use a fresh ChatGPT tool-discovery context before any future transport retest.
