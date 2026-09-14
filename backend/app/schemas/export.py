from enum import Enum
from typing import Optional
import uuid
from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    PDF = "pdf"
    PPTX = "pptx"


class ExportRequestSchema(BaseModel):
    """
    Server-authoritative export request schema.
    Resolves generated content server-side via transformation_id.
    """
    transformation_id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the server-generated transformation result to export",
    )
    export_format: ExportFormat = Field(
        ...,
        description="Target export file format: 'pdf' or 'pptx'",
    )
    document_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional document UUID constraint",
    )
    include_provenance: bool = Field(
        default=True,
        description="Whether to append source citations and chunk provenance to the export",
    )
    include_verification: bool = Field(
        default=True,
        description="Whether to embed verification status and verdict breakdown if verified",
    )
