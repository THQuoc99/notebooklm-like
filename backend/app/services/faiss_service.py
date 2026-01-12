import faiss
import numpy as np
import os
import threading
from typing import List, Tuple
from app.config import settings
from pymongo import MongoClient
from datetime import datetime
import platform
import logging

logger = logging.getLogger(__name__)


def _to_short_path(path: str) -> str:
    """Return a short (8.3) path on Windows, otherwise return original path."""
    if platform.system().lower().startswith("win"):
        try:
            import ctypes
            GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
            GetShortPathNameW.argtypes = [
                ctypes.c_wchar_p,
                ctypes.c_wchar_p,
                ctypes.c_uint,
            ]
            GetShortPathNameW.restype = ctypes.c_uint

            buf_size = GetShortPathNameW(path, None, 0)
            if buf_size == 0:
                return path

            buf = ctypes.create_unicode_buffer(buf_size)
            res = GetShortPathNameW(path, buf, buf_size)
            if res == 0:
                return path

            return buf.value
        except Exception:
            return path
    return path


class FAISSService:
    def __init__(self):
        self.index_path = settings.FAISS_INDEX_PATH
        self.dimension = settings.EMBEDDING_DIM
        self.index = None
        self.current_id = 0
        self.lock = threading.Lock()
        
        # Check CUDA availability
        self.use_gpu = False
        try:
            num_gpus = faiss.get_num_gpus()
            if num_gpus > 0:
                self.use_gpu = True
                logger.info(f"✅ CUDA detected: {num_gpus} GPU(s) available for FAISS")
                print(f"✅ CUDA detected: {num_gpus} GPU(s) available for FAISS")
            else:
                logger.warning("⚠️ No CUDA GPUs found - FAISS will run on CPU")
                print("⚠️ No CUDA GPUs found - FAISS will run on CPU")
        except Exception as e:
            logger.warning(f"⚠️ CUDA check failed: {e} - FAISS will run on CPU")
            print(f"⚠️ CUDA check failed: {e} - FAISS will run on CPU")

        # MongoDB for metadata
        self.mongo_client = MongoClient(settings.MONGO_URL)
        self.db = self.mongo_client[settings.MONGO_DB]
        self.faiss_meta_col = self.db["faiss_meta"]

        self._load_or_create_index()

    def _load_or_create_index(self):
        """Load existing index or create new one."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

        if os.path.exists(self.index_path):
            try:
                print(f"Loading FAISS index from {self.index_path}")
                read_path = _to_short_path(self.index_path)
                self.index = faiss.read_index(read_path)

                meta = self.faiss_meta_col.find_one(
                    {"index_name": "notebooklm_index"}
                )
                if meta:
                    self.current_id = meta.get("total_vectors", 0)
                else:
                    self.current_id = self.index.ntotal
            except Exception as e:
                print(f"Error loading index: {e}. Creating new index...")
                self._create_new_index()
        else:
            print("Creating new FAISS index")
            self._create_new_index()

    def _create_new_index(self):
        """Create a new FAISS index with ID mapping support."""
        base_index = faiss.IndexFlatIP(self.dimension)
        self.index = faiss.IndexIDMap2(base_index)
        self.current_id = 0
        print(
            f"Created new FAISS IndexIDMap2(IndexFlatIP) with dimension {self.dimension}"
        )

    def add_vectors(self, vectors: List[List[float]]) -> List[int]:
        """Add vectors with explicit IDs. Returns list of FAISS IDs."""
        if not vectors:
            return []

        vectors_np = np.array(vectors, dtype="float32")
        faiss.normalize_L2(vectors_np)

        with self.lock:
            start_id = self.current_id
            ids = np.arange(
                start_id, start_id + len(vectors), dtype="int64"
            )
            self.index.add_with_ids(vectors_np, ids)
            self.current_id += len(vectors)
            logger.info(
                f"Added {len(vectors)} vectors with IDs {start_id} to {self.current_id - 1}"
            )

        return ids.tolist()

    def search(
        self, query_vector: List[float], k: int = 5
    ) -> Tuple[List[int], List[float]]:
        query_np = np.array([query_vector], dtype="float32")
        faiss.normalize_L2(query_np)

        with self.lock:
            scores, indices = self.index.search(query_np, k)

        return indices[0].tolist(), scores[0].tolist()

    def remove_ids(self, ids: List[int]) -> int:
        """Remove vectors by IDs. Returns number removed."""
        if not ids:
            return 0
        try:
            with self.lock:
                ids_array = np.array(ids, dtype="int64")
                n_removed = self.index.remove_ids(ids_array)
                logger.info(f"Removed {n_removed} vectors from FAISS")
                return int(n_removed)
        except Exception as e:
            logger.error(f"Failed to remove IDs: {e}")
            raise

    def save(self):
        """Alias for save_index for backward compatibility."""
        self.save_index()

    def save_index(self):
        with self.lock:
            try:
                index_dir = os.path.dirname(self.index_path)
                os.makedirs(index_dir, exist_ok=True)

                logger.info(f"Saving FAISS index to: {self.index_path}")
                print(f"Saving FAISS index to: {self.index_path}")
                print(f"Directory exists: {os.path.exists(index_dir)}")

                write_path = _to_short_path(self.index_path)
                print(f"Using write path: {write_path}")

                faiss.write_index(self.index, write_path)

                logger.info("FAISS index saved successfully")
                print("FAISS index saved successfully")

            except Exception as e:
                logger.error(f"Error saving FAISS index: {e}")
                print(f"Error saving FAISS index: {e}")
                raise

        self.faiss_meta_col.update_one(
            {"index_name": "notebooklm_index"},
            {
                "$set": {
                    "index_name": "notebooklm_index",
                    "index_type": "IndexIDMap2",
                    "embedding_dim": self.dimension,
                    "total_vectors": self.current_id,
                    "faiss_file_path": self.index_path,
                    "last_updated": datetime.utcnow(),
                }
            },
            upsert=True,
        )

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_type": "IndexIDMap2(IndexFlatIP)",
        }


faiss_service = FAISSService()
