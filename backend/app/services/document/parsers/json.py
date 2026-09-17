import json
import asyncio
from typing import List, Any, Dict, Optional
from app.services.document.parsers.base import BaseDocumentParser
from app.services.document.models import ParsedDocument, DocumentElement, ElementType, SourceModality


class JSONDocumentParser(BaseDocumentParser):
    """
    Parser for JSON files (.json).
    Parses objects, arrays, and nested structures into structured DocumentElements with JSON path provenance.
    """

    @property
    def supported_extensions(self) -> List[str]:
        return [".json"]

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        def _parse_sync() -> ParsedDocument:
            # 1. Decode text
            text = None
            for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252", "utf-16"):
                try:
                    text = file_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if text is None:
                text = file_bytes.decode("utf-8", errors="replace")

            if not text.strip():
                raise ValueError(f"Uploaded JSON file '{filename}' is empty.")

            # 2. Parse JSON safely
            try:
                data = json.loads(text)
            except Exception as e:
                raise ValueError(f"Invalid JSON in file '{filename}': {e}") from e

            elements: List[DocumentElement] = []

            # 3. Recursively extract structured elements preserving JSON path provenance
            def _flatten_json(obj: Any, path: str = "") -> List[DocumentElement]:
                local_elements: List[DocumentElement] = []

                if isinstance(obj, dict):
                    if not obj:
                        section_name = path or "Root"
                        local_elements.append(
                            DocumentElement(
                                element_type=ElementType.PARAGRAPH,
                                text=f"{section_name}: {{}}",
                                section_title=section_name,
                                metadata={"filename": filename, "json_path": path, "type": "empty_object"},
                            )
                        )
                        return local_elements

                    # Group scalar key-values and recurse for complex items
                    scalar_pairs = []
                    complex_items = []
                    for k, v in obj.items():
                        child_path = f"{path}.{k}" if path else str(k)
                        if isinstance(v, (dict, list)):
                            complex_items.append((k, v, child_path))
                        else:
                            scalar_pairs.append((k, v, child_path))

                    if scalar_pairs:
                        section_name = path or "Root"
                        formatted_text = "\n".join(f"{k}: {v}" for k, v, _ in scalar_pairs)
                        local_elements.append(
                            DocumentElement(
                                element_type=ElementType.PARAGRAPH,
                                text=formatted_text,
                                section_title=section_name,
                                metadata={
                                    "filename": filename,
                                    "json_path": path or "root",
                                    "fields": [p[0] for p in scalar_pairs],
                                },
                            )
                        )

                    for k, v, child_path in complex_items:
                        local_elements.extend(_flatten_json(v, child_path))

                elif isinstance(obj, list):
                    if not obj:
                        section_name = path or "List"
                        local_elements.append(
                            DocumentElement(
                                element_type=ElementType.PARAGRAPH,
                                text=f"{section_name}: []",
                                section_title=section_name,
                                metadata={"filename": filename, "json_path": path, "type": "empty_list"},
                            )
                        )
                        return local_elements

                    # Check if list is all primitive/scalar
                    all_scalar = all(not isinstance(item, (dict, list)) for item in obj)
                    if all_scalar:
                        section_name = path or "List"
                        formatted_text = f"{section_name}:\n" + "\n".join(f"- {item}" for item in obj)
                        local_elements.append(
                            DocumentElement(
                                element_type=ElementType.LIST_ITEM,
                                text=formatted_text,
                                section_title=section_name,
                                metadata={"filename": filename, "json_path": path, "item_count": len(obj)},
                            )
                        )
                    else:
                        for idx, item in enumerate(obj):
                            item_path = f"{path}[{idx}]" if path else f"[{idx}]"
                            local_elements.extend(_flatten_json(item, item_path))

                else:
                    # Primitive value at root
                    section_name = path or "Value"
                    local_elements.append(
                        DocumentElement(
                            element_type=ElementType.PARAGRAPH,
                            text=f"{section_name}: {obj}",
                            section_title=section_name,
                            metadata={"filename": filename, "json_path": path},
                        )
                    )

                return local_elements

            elements = _flatten_json(data)
            if not elements:
                elements.append(
                    DocumentElement(
                        element_type=ElementType.PARAGRAPH,
                        text=json.dumps(data, indent=2),
                        section_title="JSON Data",
                        metadata={"filename": filename, "json_path": "root"},
                    )
                )

            # Format raw text nicely
            try:
                formatted_raw_text = json.dumps(data, indent=2, ensure_ascii=False)
            except Exception:
                formatted_raw_text = text

            return ParsedDocument(
                elements=elements,
                raw_text=formatted_raw_text,
                page_count=1,
                modality=SourceModality.TEXT,
                metadata={"filename": filename, "format": "json"},
            )

        return await asyncio.to_thread(_parse_sync)


# Alias
JSONParser = JSONDocumentParser
