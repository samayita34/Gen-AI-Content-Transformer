import logging
from fastapi import APIRouter, HTTPException, status, Response

from app.schemas.export import ExportRequestSchema, ExportFormat
from app.services.generation.store import default_result_store
from app.services.export.service import default_export_service

logger = logging.getLogger("transformai.api.export")
router = APIRouter()


@router.post(
    "/export",
    summary="Export Generated Transformation Result",
    description=(
        "Exports a server-cached transformation result to PDF or PPTX. "
        "Strictly server-authoritative: resolves content from the server session by transformation_id."
    ),
    responses={
        200: {
            "description": "Document binary file (PDF or PPTX)",
            "content": {
                "application/pdf": {},
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": {},
            },
        },
        404: {"description": "Transformation result not found"},
        422: {"description": "Invalid format or generation output mismatch"},
    },
)
async def export_transformation(request: ExportRequestSchema) -> Response:
    # 1. Authoritative server lookup
    result = default_result_store.get_result(request.transformation_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Transformation result with ID '{request.transformation_id}' was not found. "
                "Exports must originate from an existing server generation run."
            ),
        )

    # 2. Check optional document ID match
    if request.document_id and result.document_id != request.document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplied document_id does not match the transformation record.",
        )

    # 3. Retrieve linked verification report if requested
    verification_report = None
    if request.include_verification:
        verification_report = default_result_store.get_verification_report(request.transformation_id)

    # 4. Generate document binary
    try:
        file_bytes = default_export_service.generate_export(
            result=result,
            export_format=request.export_format.value,
            verification_report=verification_report,
            include_provenance=request.include_provenance,
            include_verification=request.include_verification,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error("Export generation failed for transformation %s: %s", request.transformation_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export generation failed: {str(exc)}",
        )

    # 5. Determine headers and filename
    short_id = str(result.transformation_id)[:8]
    fmt = request.export_format.value
    if fmt == "pptx":
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        filename = f"transformai_presentation_{short_id}.pptx"
    else:
        media_type = "application/pdf"
        filename = f"transformai_{result.output_type.value}_{short_id}.pdf"

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
