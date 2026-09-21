from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import Field, model_validator

from albayan_mcp.schemas.document2 import (
    Document2ContractModel,
    DocumentCitationInlineToken,
    DocumentInlineAnchor,
    DocumentMathInlineToken,
    DocumentReferenceInlineToken,
    DocumentTextInlineToken,
    InsertBibliographyCommand,
    InsertFigureCommand,
    InsertListCommand,
    InsertListItemCommand,
    InsertReferenceCommand,
    InsertTableColumnCommand,
    InsertTableCommand,
    InsertTableRowCommand,
    InsertTextBlockCommand,
    MoveBlockCommand,
    MoveListItemCommand,
    MoveReferenceCommand,
    MoveTableColumnCommand,
    MoveTableRowCommand,
    NonBlankString,
    RemoveBlockCommand,
    RemoveInlineTokenCommand,
    RemoveListItemCommand,
    RemoveReferenceCommand,
    RemoveTableColumnCommand,
    RemoveTableRowCommand,
    ReplaceListItemCommand,
    ReplaceTableCellCommand,
    ReplaceTextBlockCommand,
    UpdateDocumentMetaCommand,
    UpdateFigureCommand,
    UpdateFloatMetaCommand,
    UpdateReferenceCommand,
)


class DocumentMathAuthoringInlineToken(Document2ContractModel):
    nullable_fields: ClassVar[frozenset[str]] = frozenset({"label"})

    kind: Literal["math"]
    latex: Annotated[NonBlankString, Field(max_length=8000)]
    display: bool = False
    label: Annotated[str, Field(max_length=500)] | None = None

    @model_validator(mode="after")
    def _label_requires_display_math(self):
        if self.label is not None and self.label.strip() and not self.display:
            raise ValueError("وسم المعادلة متاح للمعادلات المستقلة فقط.")
        return self


DocumentDraftInlineTokenInput = (
    DocumentTextInlineToken
    | DocumentMathInlineToken
    | DocumentMathAuthoringInlineToken
    | DocumentCitationInlineToken
    | DocumentReferenceInlineToken
)


class InsertInlineTokenCommand(Document2ContractModel):
    op: Literal["insert_inline_token"]
    field_id: NonBlankString
    token: DocumentDraftInlineTokenInput
    anchor: DocumentInlineAnchor


class ReplaceInlineTokenCommand(Document2ContractModel):
    op: Literal["replace_inline_token"]
    field_id: NonBlankString
    token_id: NonBlankString
    token: DocumentDraftInlineTokenInput


DocumentCommand = Annotated[
    InsertTextBlockCommand
    | ReplaceTextBlockCommand
    | RemoveBlockCommand
    | MoveBlockCommand
    | InsertFigureCommand
    | UpdateFigureCommand
    | UpdateFloatMetaCommand
    | InsertBibliographyCommand
    | UpdateDocumentMetaCommand
    | InsertReferenceCommand
    | UpdateReferenceCommand
    | RemoveReferenceCommand
    | MoveReferenceCommand
    | InsertInlineTokenCommand
    | ReplaceInlineTokenCommand
    | RemoveInlineTokenCommand
    | InsertListCommand
    | InsertListItemCommand
    | ReplaceListItemCommand
    | RemoveListItemCommand
    | MoveListItemCommand
    | InsertTableCommand
    | ReplaceTableCellCommand
    | InsertTableRowCommand
    | RemoveTableRowCommand
    | MoveTableRowCommand
    | InsertTableColumnCommand
    | RemoveTableColumnCommand
    | MoveTableColumnCommand,
    Field(discriminator="op"),
]
