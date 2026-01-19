"""In-memory job queue for async processing."""
from typing import Dict, Tuple, Any, Optional
from enum import Enum
import threading
from datetime import datetime


class JobStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class JobQueue:
    """Thread-safe in-memory job tracker."""
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def create_job(self, job_id: str, filename: str, api_key_hash: Optional[str] = None) -> None:
        """
        Create a new job entry.
        
        Args:
            job_id: Unique job identifier
            filename: Original filename
            api_key_hash: Hash of API key (for ownership tracking)
        """
        with self._lock:
            self._jobs[job_id] = {
                "status": JobStatus.PROCESSING,
                "filename": filename,
                "api_key_hash": api_key_hash,
                "result": None,
                "error": None,
                "created_at": datetime.now().isoformat()
            }
    
    def set_result(self, job_id: str, result: Any) -> None:
        """Mark job as completed with result."""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.COMPLETED
                self._jobs[job_id]["result"] = result
                self._jobs[job_id]["completed_at"] = datetime.now().isoformat()
    
    def set_error(self, job_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.ERROR
                self._jobs[job_id]["error"] = error
                self._jobs[job_id]["completed_at"] = datetime.now().isoformat()
    
    def get_status(self, job_id: str) -> Tuple[str, Optional[Any]]:
        """Get job status and data."""
        with self._lock:
            if job_id not in self._jobs:
                return ("notfound", None)
            
            job = self._jobs[job_id]
            status = job["status"].value
            
            if status == "completed":
                return (status, job["result"])
            elif status == "error":
                return (status, job["error"])
            else:
                return (status, None)
    
    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get full job information including metadata."""
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
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            job = self._jobs[job_id]
            return job.get("api_key_hash") == api_key_hash

