"""Typed host mirror of the BuTeX 7.0.2 ``Document2Command`` contract."""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


def _non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("يجب ألا تكون القيمة فارغة.")
    return value


NonBlankString = Annotated[str, AfterValidator(_non_blank)]
NonNegativeIndex = Annotated[int, Field(ge=0)]


class Document2ContractModel(BaseModel):
    """Strict wire model: validate without coercing or silently dropping fields."""

    model_config = ConfigDict(extra="forbid", strict=True)
    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _reject_explicit_null_for_optional_wire_fields(self):
        for field_name in self.model_fields_set:
            if (
                getattr(self, field_name) is None
                and field_name not in self.nullable_fields
            ):
                raise ValueError(
                    f"{field_name} لا يقبل null عند إرساله."
                )
        return self


class DocumentBlockMetadata(Document2ContractModel):
    source: Literal["agent", "user"] | None = None


class DocumentAnchor(Document2ContractModel):
    before_block_id: NonBlankString | None = None
    after_block_id: NonBlankString | None = None
    end: Literal[True] | None = None

    @model_validator(mode="after")
    def _exactly_one_anchor(self):
        choices = sum(
            value is not None
            for value in (self.before_block_id, self.after_block_id, self.end)
        )
        if choices != 1:
            raise ValueError(
                "حدد before_block_id أو after_block_id أو end: true فقط."
            )
        return self


class DocumentInlineAnchor(Document2ContractModel):
    before_token_id: NonBlankString | None = None
    after_token_id: NonBlankString | None = None
    start: Literal[True] | None = None
    end: Literal[True] | None = None

    @model_validator(mode="after")
    def _exactly_one_anchor(self):
        choices = sum(
            value is not None
            for value in (
                self.before_token_id,
                self.after_token_id,
                self.start,
                self.end,
            )
        )
        if choices != 1:
            raise ValueError("حدد موضع رمز مضمّن واحدًا فقط.")
        return self


class DocumentListItemAnchor(Document2ContractModel):
    before_item_id: NonBlankString | None = None
    after_item_id: NonBlankString | None = None
    end: Literal[True] | None = None

    @model_validator(mode="after")
    def _exactly_one_anchor(self):
        choices = sum(
            value is not None
            for value in (self.before_item_id, self.after_item_id, self.end)
        )
        if choices != 1:
            raise ValueError("حدد موضع عنصر قائمة واحدًا فقط.")
        return self


class DocumentReferenceAnchor(Document2ContractModel):
    before_reference_key: NonBlankString | None = None
    after_reference_key: NonBlankString | None = None
    end: Literal[True] | None = None

    @model_validator(mode="after")
    def _exactly_one_anchor(self):
        choices = sum(
            value is not None
            for value in (
                self.before_reference_key,
                self.after_reference_key,
                self.end,
            )
        )
        if choices != 1:
            raise ValueError("حدد موضع مرجع واحدًا فقط.")
        return self


class DocumentTextStyle(Document2ContractModel):
    bold: Literal[True] | None = None
    italic: Literal[True] | None = None
    underline: Literal[True] | None = None


class DocumentMathNodeJson(Document2ContractModel):
    """Recursive BuTeX equation AST node carried by a structured math token."""

    nullable_fields: ClassVar[frozenset[str]] = frozenset(
        {"superscript", "subscript"}
    )

    node_type: str
    expr: str | None = None
    name: str | None = None
    superscript: DocumentMathChainJson | None = None
    subscript: DocumentMathChainJson | None = None
    left_delim_expr: str | None = None
    right_delim_expr: str | None = None
    inner_expr: DocumentMathChainJson | None = None
    optional_args: list[DocumentMathChainJson] | None = None
    mandatory_args: list[DocumentMathChainJson] | None = None
    opening: str | None = None
    closing: str | None = None
    lines: list[DocumentMathChainJson] | None = None


class DocumentMathChainJson(Document2ContractModel):
    node_type: Literal["ChainClass"]
    chain: list[DocumentMathNodeJson]


DocumentParseMode = Literal["english", "arabic"]


class DocumentMathObjectJson(Document2ContractModel):
    node_type: Literal["MathObject"]
    math_mode: str
    lines: list[DocumentMathChainJson]
    closing: str
    source_side: DocumentParseMode | None = None
    source_owner: Literal["imported-structured", "editor"] | None = None
    label_enabled: bool | None = None
    label: str | None = None


class DocumentTextInlineToken(Document2ContractModel):
    kind: Literal["text"]
    text: str
    style: DocumentTextStyle | None = None


class DocumentMathInlineToken(Document2ContractModel):
    kind: Literal["math"]
    source: NonBlankString
    math_object: DocumentMathObjectJson


def _require_non_empty_key(keys: list[str]) -> list[str]:
    if not any(key.strip() for key in keys):
        raise ValueError(
            "يجب تحديد مفتاح واحد غير فارغ على الأقل."
        )
    return keys


DocumentReferenceKeys = Annotated[
    list[str],
    Field(min_length=1),
    AfterValidator(_require_non_empty_key),
]


class DocumentCitationInlineToken(Document2ContractModel):
    kind: Literal["cite"]
    keys: DocumentReferenceKeys


class DocumentReferenceInlineToken(Document2ContractModel):
    kind: Literal["ref"]
    keys: DocumentReferenceKeys
    ref_command: Literal["ref", "eqref"]


DocumentInlineTokenInput = Annotated[
    DocumentTextInlineToken
    | DocumentMathInlineToken
    | DocumentCitationInlineToken
    | DocumentReferenceInlineToken,
    Field(discriminator="kind"),
]

DocumentTextKind = Literal["section", "subsection", "subsubsection", "paragraph"]


class InsertTextBlockCommand(Document2ContractModel):
    op: Literal["insert_text_block"]
    kind: DocumentTextKind
    text: str
    anchor: DocumentAnchor
    metadata: DocumentBlockMetadata | None = None


class ReplaceTextBlockCommand(Document2ContractModel):
    op: Literal["replace_text_block"]
    block_id: NonBlankString
    text: str


class RemoveBlockCommand(Document2ContractModel):
    op: Literal["remove_block"]
    block_id: NonBlankString


class MoveBlockCommand(Document2ContractModel):
    op: Literal["move_block"]
    block_id: NonBlankString
    anchor: DocumentAnchor


class InsertFigureCommand(Document2ContractModel):
    op: Literal["insert_figure"]
    asset_id: NonBlankString
    value: str | None = None
    caption: str | None = None
    label: str | None = None
    anchor: DocumentAnchor
    metadata: DocumentBlockMetadata | None = None


class UpdateFigureCommand(Document2ContractModel):
    nullable_fields: ClassVar[frozenset[str]] = frozenset({"asset_id"})

    op: Literal["update_figure"]
    block_id: NonBlankString
    asset_id: NonBlankString | None = None
    value: str | None = None

    @model_validator(mode="after")
    def _at_least_one_patch_field(self):
        if not self.model_fields_set.intersection({"asset_id", "value"}):
            raise ValueError("update_figure يتطلب asset_id أو value.")
        return self


class UpdateFloatMetaCommand(Document2ContractModel):
    op: Literal["update_float_meta"]
    block_id: NonBlankString
    centered: bool | None = None
    caption_enabled: bool | None = None
    caption: str | None = None
    label_enabled: bool | None = None
    label: str | None = None

    @model_validator(mode="after")
    def _at_least_one_patch_field(self):
        patch_fields = {
            "centered",
            "caption_enabled",
            "caption",
            "label_enabled",
            "label",
        }
        if not self.model_fields_set.intersection(patch_fields):
            raise ValueError(
                "update_float_meta يتطلب حقل تعديل واحدًا."
            )
        return self


class InsertBibliographyCommand(Document2ContractModel):
    op: Literal["insert_bibliography"]
    anchor: DocumentAnchor
    metadata: DocumentBlockMetadata | None = None


HijriMonthId = Literal[
    "محرم",
    "صفر",
    "ربيع الأول",
    "ربيع الآخر",
    "جمادى الأولى",
    "جمادى الآخرة",
    "رجب",
    "شعبان",
    "رمضان",
    "شوال",
    "ذو القعدة",
    "ذو الحجة",
]


class DocumentHijriDatePatch(Document2ContractModel):
    day: Annotated[int, Field(ge=1, le=30)] | None = None
    month: HijriMonthId | None = None
    year: Annotated[int, Field(ge=1400, le=1500)] | None = None

    @model_validator(mode="after")
    def _at_least_one_date_field(self):
        if not self.model_fields_set.intersection({"day", "month", "year"}):
            raise ValueError(
                "تحديث التاريخ يتطلب حقلًا واحدًا على الأقل."
            )
        return self


class UpdateDocumentMetaCommand(Document2ContractModel):
    op: Literal["update_document_meta"]
    title: str | None = None
    authors: str | None = None
    abstract: str | None = None
    date: DocumentHijriDatePatch | None = None

    @model_validator(mode="after")
    def _at_least_one_patch_field(self):
        if not self.model_fields_set.intersection(
            {"title", "authors", "abstract", "date"}
        ):
            raise ValueError(
                "update_document_meta يتطلب حقل تعديل واحدًا."
            )
        return self


ReferenceFieldSeparator = Literal[",", "،"]


class InsertReferenceCommand(Document2ContractModel):
    op: Literal["insert_reference"]
    key: NonBlankString
    authors: str | None = None
    title: str | None = None
    year: str | None = None
    venue: str | None = None
    url: str | None = None
    field_separator: ReferenceFieldSeparator | None = None
    anchor: DocumentReferenceAnchor


class UpdateReferenceCommand(Document2ContractModel):
    op: Literal["update_reference"]
    reference_key: NonBlankString
    key: str | None = None
    authors: str | None = None
    title: str | None = None
    year: str | None = None
    venue: str | None = None
    url: str | None = None
    field_separator: ReferenceFieldSeparator | None = None

    @model_validator(mode="after")
    def _at_least_one_patch_field(self):
        patch_fields = {
            "key",
            "authors",
            "title",
            "year",
            "venue",
            "url",
            "field_separator",
        }
        if not self.model_fields_set.intersection(patch_fields):
            raise ValueError(
                "update_reference يتطلب حقل تعديل واحدًا."
            )
        return self


class RemoveReferenceCommand(Document2ContractModel):
    op: Literal["remove_reference"]
    reference_key: NonBlankString


class MoveReferenceCommand(Document2ContractModel):
    op: Literal["move_reference"]
    reference_key: NonBlankString
    anchor: DocumentReferenceAnchor


class InsertInlineTokenCommand(Document2ContractModel):
    op: Literal["insert_inline_token"]
    field_id: NonBlankString
    token: DocumentInlineTokenInput
    anchor: DocumentInlineAnchor


class ReplaceInlineTokenCommand(Document2ContractModel):
    op: Literal["replace_inline_token"]
    field_id: NonBlankString
    token_id: NonBlankString
    token: DocumentInlineTokenInput


class RemoveInlineTokenCommand(Document2ContractModel):
    op: Literal["remove_inline_token"]
    field_id: NonBlankString
    token_id: NonBlankString


class InsertListCommand(Document2ContractModel):
    op: Literal["insert_list"]
    ordered: bool
    items: Annotated[list[str], Field(min_length=1)]
    anchor: DocumentAnchor
    metadata: DocumentBlockMetadata | None = None


class InsertListItemCommand(Document2ContractModel):
    op: Literal["insert_list_item"]
    list_id: NonBlankString
    text: str
    anchor: DocumentListItemAnchor


class ReplaceListItemCommand(Document2ContractModel):
    op: Literal["replace_list_item"]
    list_id: NonBlankString
    item_id: NonBlankString
    text: str


class RemoveListItemCommand(Document2ContractModel):
    op: Literal["remove_list_item"]
    list_id: NonBlankString
    item_id: NonBlankString


class MoveListItemCommand(Document2ContractModel):
    op: Literal["move_list_item"]
    list_id: NonBlankString
    item_id: NonBlankString
    anchor: DocumentListItemAnchor


class InsertTableCommand(Document2ContractModel):
    op: Literal["insert_table"]
    rows: Annotated[list[list[str]], Field(min_length=1)]
    columns: NonBlankString
    caption: str | None = None
    label: str | None = None
    anchor: DocumentAnchor
    metadata: DocumentBlockMetadata | None = None

    @model_validator(mode="after")
    def _rectangular_non_empty_rows(self):
        column_count = len(self.rows[0])
        if column_count == 0 or any(len(row) != column_count for row in self.rows):
            raise ValueError(
                "يجب أن تكون صفوف الجدول مستطيلة وغير فارغة."
            )
        return self


class ReplaceTableCellCommand(Document2ContractModel):
    op: Literal["replace_table_cell"]
    table_id: NonBlankString
    row_index: NonNegativeIndex
    column_index: NonNegativeIndex
    text: str


class InsertTableRowCommand(Document2ContractModel):
    op: Literal["insert_table_row"]
    table_id: NonBlankString
    index: NonNegativeIndex
    values: list[str]


class RemoveTableRowCommand(Document2ContractModel):
    op: Literal["remove_table_row"]
    table_id: NonBlankString
    index: NonNegativeIndex


class MoveTableRowCommand(Document2ContractModel):
    op: Literal["move_table_row"]
    table_id: NonBlankString
    from_index: NonNegativeIndex
    to_index: NonNegativeIndex


class InsertTableColumnCommand(Document2ContractModel):
    op: Literal["insert_table_column"]
    table_id: NonBlankString
    index: NonNegativeIndex
    values: list[str]
    columns: NonBlankString


class RemoveTableColumnCommand(Document2ContractModel):
    op: Literal["remove_table_column"]
    table_id: NonBlankString
    index: NonNegativeIndex
    columns: NonBlankString


class MoveTableColumnCommand(Document2ContractModel):
    op: Literal["move_table_column"]
    table_id: NonBlankString
    from_index: NonNegativeIndex
    to_index: NonNegativeIndex
    columns: NonBlankString


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


BLOCK_INSERTION_OPERATIONS = frozenset(
    {
        "insert_text_block",
        "insert_figure",
        "insert_bibliography",
        "insert_list",
        "insert_table",
    }
)
