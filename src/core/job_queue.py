"""In-memory job queue for async processing with optional KV store backend."""
from typing import Dict, Tuple, Any, Optional
from enum import Enum
import threading
from datetime import datetime
import json


class JobStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class JobQueue:
    """Thread-safe job tracker with optional KV store for distributed state."""
    
    def __init__(self, kv_store=None):
        """
        Initialize job queue.
        
        Args:
            kv_store: Optional Modal KV store for distributed state.
                      If None, uses in-memory only (single container).
        """
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.kv_store = kv_store  # Modal KVNamespace for distributed state
    
    def _serialize_job(self, job: Dict[str, Any]) -> str:
        """Serialize job to JSON for storage."""
        job_copy = job.copy()
        return json.dumps(job_copy, default=str)
    
    def _deserialize_job(self, data: str) -> Dict[str, Any]:
        """Deserialize job from JSON."""
        return json.loads(data)
    
    def create_job(self, job_id: str, filename: str, api_key_hash: Optional[str] = None) -> None:
        """
        Create a new job entry.
        
        Args:
            job_id: Unique job identifier
            filename: Original filename
            api_key_hash: Hash of API key (for ownership tracking)
        """
        job = {
            "status": JobStatus.PROCESSING.value,
            "filename": filename,
            "api_key_hash": api_key_hash,
            "result": None,
            "error": None,
            "created_at": datetime.now().isoformat()
        }
        with self._lock:
            self._jobs[job_id] = job
        
        # Store in KV if available
        if self.kv_store:
            try:
                self.kv_store[job_id] = job
            except Exception as e:
                # Fallback to in-memory if storage fails
                pass
    
    def set_result(self, job_id: str, result: Any) -> None:
        """Mark job as completed with result."""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.COMPLETED.value
                self._jobs[job_id]["result"] = result
                self._jobs[job_id]["completed_at"] = datetime.now().isoformat()
                
                # Update in KV if available
                if self.kv_store:
                    try:
                        self.kv_store[job_id] = self._jobs[job_id]
                    except Exception:
                        pass
    
    def set_error(self, job_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.ERROR.value
                self._jobs[job_id]["error"] = error
                self._jobs[job_id]["completed_at"] = datetime.now().isoformat()
                
                # Update in KV if available
                if self.kv_store:
                    try:
                        self.kv_store[job_id] = self._jobs[job_id]
                    except Exception:
                        pass
    
    def get_status(self, job_id: str) -> Tuple[str, Optional[Any]]:
        """Get job status and data, checking KV first if available."""
        # Try KV store first (distributed state)
        if self.kv_store:
            try:
                job = self.kv_store.get(job_id)
                if job:
                    status = job.get("status", "notfound")
                    if status == "completed":
                        return (status, job.get("result"))
                    elif status == "error":
                        return (status, job.get("error"))
                    else:
                        return (status, None)
            except Exception:
                pass  # Fallback to in-memory
        
        # Fallback to in-memory
        with self._lock:
            if job_id not in self._jobs:
                return ("notfound", None)
            
            job = self._jobs[job_id]
            status = job["status"] if isinstance(job["status"], str) else job["status"].value
            
            if status == "completed":
                return (status, job["result"])
            elif status == "error":
                return (status, job["error"])
            else:
                return (status, None)
    
    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get full job information, checking KV first if available."""
        # Try KV store first
        if self.kv_store:
            try:
                job = self.kv_store.get(job_id)
                if job:
                    return job
            except Exception:
                pass
        
        # Fallback to in-memory
        with self._lock:
            return self._jobs.get(job_id)
    
    def verify_job_ownership(self, job_id: str, api_key_hash: str) -> bool:
        """
        Verify that a job belongs to the given API key.
        
        Args:
            job_id: Job identifier
            api_key_hash: Hash of the API key
            
        Returns:
            True if job belongs to this key, False otherwise
        """
        job = self.get_job_info(job_id)
        if not job:
            return False
        
        return job.get("api_key_hash") == api_key_hash

