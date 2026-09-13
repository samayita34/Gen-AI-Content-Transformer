import asyncio
import os
import uuid
from abc import ABC, abstractmethod
from typing import BinaryIO, Union
from pathlib import Path


class BaseDocumentStorage(ABC):
    """
    Abstract storage interface for raw ingested document files.
    Allows seamlessly swapping local disk storage for S3 or Supabase Storage.
    """

    @abstractmethod
    async def save_file(self, file_content: bytes, original_filename: str) -> str:
        """Saves file content and returns a unique storage key."""
        pass

    @abstractmethod
    async def get_file_bytes(self, storage_key: str) -> bytes:
        """Reads file bytes from storage given its storage key."""
        pass

    @abstractmethod
    async def get_file_path(self, storage_key: str) -> str:
        """Returns local filesystem path for parsers requiring a file path."""
        pass

    @abstractmethod
    async def delete_file(self, storage_key: str) -> bool:
        """Deletes file from storage."""
        pass


class LocalDocumentStorage(BaseDocumentStorage):
    """
    Local filesystem implementation of Document Storage.
    """

    def __init__(self, base_dir: str = "storage/documents"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_content: bytes, original_filename: str) -> str:
        ext = Path(original_filename).suffix.lower()
        unique_id = uuid.uuid4().hex
        storage_key = f"{unique_id}{ext}"
        destination = self.base_dir / storage_key

        def _write():
            with open(destination, "wb") as f:
                f.write(file_content)

        await asyncio.to_thread(_write)
        return storage_key

    async def get_file_bytes(self, storage_key: str) -> bytes:
        file_path = self.base_dir / storage_key
        if not file_path.exists():
            raise FileNotFoundError(f"Storage key {storage_key} not found.")

        def _read():
            with open(file_path, "rb") as f:
                return f.read()

        return await asyncio.to_thread(_read)

    async def get_file_path(self, storage_key: str) -> str:
        file_path = self.base_dir / storage_key
        if not file_path.exists():
            raise FileNotFoundError(f"Storage key {storage_key} not found.")
        return str(file_path.resolve())

    async def delete_file(self, storage_key: str) -> bool:
        file_path = self.base_dir / storage_key
        if file_path.exists():
            await asyncio.to_thread(file_path.unlink)
            return True
        return False


# Global default storage instance
default_storage = LocalDocumentStorage()
