# MCP binary/file transport probe

`test_mcp_content_transport` is a temporary, self-contained diagnostic tool for comparing
MCP Inspector and ChatGPT handling of non-JSON tool content. It does **not** call FastAPI,
S3/object storage, Butex, or the compiler.

The tool uses a fixed 75-byte 2x2 PNG, a fixed 608-byte one-page PDF, a tiny binary blob,
and a fixed text resource. The same fixtures are returned every time.

## Test matrix

Call the same tool once per `case` and record what the client/model can actually see or
surface.

| case | MCP content returned | Question answered |
| --- | --- | --- |
| `image_content` | image-only `ImageContent(image/png)` | Does the current `get_article_asset` representation survive the bridge? |
| `image_content_with_text` | `TextContent` + `ImageContent` | Does a text block make otherwise-dropped image content visible? |
| `embedded_text` | `EmbeddedResource(TextResourceContents)` | Are embedded resources generally supported when they are text? |
| `embedded_binary` | `EmbeddedResource(BlobResourceContents)` as `application/octet-stream` | Is generic binary resource content preserved? |
| `embedded_png` | `EmbeddedResource(BlobResourceContents)` as `image/png` | Is an image blob resource treated differently from `ImageContent`? |
| `embedded_pdf` | PDF-only `EmbeddedResource(BlobResourceContents)` | Exact transport class used by `get_article_pdf`, without backend/compiler variables. |
| `embedded_pdf_with_text` | `TextContent` + PDF `EmbeddedResource` | Does a text block change PDF/resource handling? |
| `upload_file_params` | sanitized `TextContent` summary | What shape did ChatGPT bind through `openai/fileParams` on web/mobile? |

For the upload case, attach a small image to the ChatGPT turn and ask it to call the probe
with `case="upload_file_params"`. The tool deliberately does not download the file and does
not echo the signed `download_url` or `file_id`. It reports only safe structural facts such
as whether those fields exist, MIME type, URL scheme, or whether the client sent a reported
`chat_upload://...` string reference.

## Suggested run order

1. Run all non-upload cases in MCP Inspector and record whether the content block is visible.
2. Run the same cases in ChatGPT (web) and record whether the model receives/renders them.
3. Repeat `upload_file_params` once in ChatGPT web with an attached image.
4. Repeat `upload_file_params` in the native mobile app with an attached image.
5. Compare only the transport boundary. If `embedded_pdf` fails here, the production PDF
   compiler/backend/storage pipeline is exonerated by construction.

## Feature flag

The probe is enabled by default by `Settings.enable_transport_probe`. Set
`ENABLE_TRANSPORT_PROBE=false` on the MCP service after the experiment to remove the tool
from discovery without changing production article behavior.
