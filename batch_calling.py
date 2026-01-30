"""
Batch Calling Service for ElevenLabs API.
Handles batch call job submission and management.
"""

from typing import Optional, Dict, Any, List

from base import BaseClient
from config import ElevenLabsConfig
from logger import APICallLogger


class BatchCallingService(BaseClient):
    """
    Service class for batch calling operations in ElevenLabs.
    
    Provides methods for:
    - Submitting batch calling jobs
    - Getting job status
    - Listing jobs
    - Cancelling jobs
    
    Example:
        >>> from config import ElevenLabsConfig
        >>> config = ElevenLabsConfig.from_env()
        >>> batch_service = BatchCallingService(config)
        >>> job = batch_service.submit_job(
        ...     call_name="Q1 Campaign",
        ...     agent_id="agent_123",
        ...     recipients=[
        ...         {"phone_number": "+14155551234", "name": "John"}
        ...     ]
        ... )
    """
    
    # API Endpoint (as per official documentation)
    BATCH_CALLING_SUBMIT_ENDPOINT = "/v1/convai/batch-calling/submit"
    BATCH_CALLING_ENDPOINT = "/v1/convai/batch-calling"
    
    def __init__(self, config: ElevenLabsConfig):
        """
        Initialize Batch Calling Service.
        
        Args:
            config: ElevenLabsConfig instance
        """
        super().__init__(config, logger_name="elevenlabs.batch_calling")
        self.logger.info("BatchCallingService initialized")
    
    def submit_job(
        self,
        call_name: str,
        agent_id: str,
        recipients: List[Dict[str, Any]],
        phone_number_id: Optional[str] = None,
        scheduled_time_unix: Optional[int] = None,
        timezone: Optional[str] = None,
        retry_count: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Submit a batch calling job to schedule calls for multiple recipients.
        
        API Endpoint: POST /v1/convai/batch-calling/submit
        
        Args:
            call_name: Name/identifier for this batch call campaign
            agent_id: ID of the agent to handle all calls
            recipients: List of recipient configurations. Each recipient can contain:
                       - phone_number: Destination phone number (required)
                       - name: Recipient name (optional)
                       - dynamic_variables: Call-specific variables (optional)
            phone_number_id: Phone number ID to use as caller ID
            scheduled_time_unix: Unix timestamp for scheduled execution
            timezone: Timezone for scheduling (e.g., "America/New_York")
            retry_count: Number of retry attempts for failed calls
            **kwargs: Additional job configuration options
            
        Returns:
            Response containing:
            - id: Batch job ID
            - phone_number_id: Phone number used
            - phone_provider: Provider type (twilio, etc.)
            - name: Job name
            - agent_id: Agent ID
            - created_at_unix: Creation timestamp
            - scheduled_time_unix: Scheduled time
            - timezone: Timezone
            - total_calls_dispatched: Number of calls started
            - total_calls_scheduled: Number of calls in queue
            - total_calls_finished: Number of completed calls
            - status: Job status (pending, running, completed, etc.)
            - retry_count: Retry configuration
            - agent_name: Name of the agent
            
        Example:
            >>> job = service.submit_job(
            ...     call_name="Customer Follow-up Campaign",
            ...     agent_id="J3Pbu5gP6NNKBscdCdwB",
            ...     recipients=[
            ...         {
            ...             "phone_number": "+14155551234",
            ...             "name": "John Doe",
            ...             "dynamic_variables": {"appointment": "2026-02-01"}
            ...         },
            ...         {
            ...             "phone_number": "+14155555678",
            ...             "name": "Jane Smith",
            ...             "dynamic_variables": {"appointment": "2026-02-02"}
            ...         }
            ...     ],
            ...     phone_number_id="ph_abc123",
            ...     retry_count=2
            ... )
            >>> print(f"Job submitted: {job['id']}, Status: {job['status']}")
        """
        with APICallLogger(self.logger, "Submit Batch Calling Job",
                          call_name=call_name, recipient_count=len(recipients)):
            payload = {
                "call_name": call_name,
                "agent_id": agent_id,
                "recipients": recipients
            }
            
            # phone_number_id is required for batch calling
            if phone_number_id:
                payload["phone_number_id"] = phone_number_id
            else:
                self.logger.error("phone_number_id is required but was not provided")
            
            if scheduled_time_unix is not None:
                payload["scheduled_time_unix"] = scheduled_time_unix
            
            if timezone is not None:
                payload["timezone"] = timezone
            
            if retry_count > 0:
                payload["retry_count"] = retry_count
            
            payload.update(kwargs)
            
            # Debug: log the payload being sent
            self.logger.info(f"Batch calling payload: {payload}")
            
            response = self._make_request(
                method="POST",
                endpoint=self.BATCH_CALLING_SUBMIT_ENDPOINT,
                data=payload
            )
            
            job_id = response.get("id", "unknown")
            status = response.get("status", "unknown")
            self.logger.info(
                f"Batch job submitted: {job_id}, "
                f"Status: {status}, "
                f"Recipients: {len(recipients)}"
            )
            return response
    
    def get_job(self, job_id: str) -> Dict[str, Any]:
        """
        Get details and status of a batch calling job.
        
        API Endpoint: GET /v1/convai/batch-calling/{job_id}
        
        Args:
            job_id: Batch job identifier
            
        Returns:
            Job details including current status and progress
            
        Example:
            >>> job = service.get_job("batch_abc123")
            >>> print(f"Status: {job['status']}")
            >>> print(f"Progress: {job['total_calls_finished']}/{job['total_calls_scheduled']}")
        """
        with APICallLogger(self.logger, "Get Batch Job", job_id=job_id):
            response = self._make_request(
                method="GET",
                endpoint=f"{self.BATCH_CALLING_ENDPOINT}/{job_id}"
            )
            
            status = response.get("status", "unknown")
            self.logger.info(f"Retrieved batch job: {job_id}, Status: {status}")
            return response
    
    def list_jobs(
        self,
        status: Optional[str] = None,
        cursor: Optional[str] = None,
        page_size: int = 30
    ) -> Dict[str, Any]:
        """
        List batch calling jobs.
        
        API Endpoint: GET /v1/convai/batch-calling
        
        Args:
            status: Filter by job status (pending, running, completed, failed)
            cursor: Pagination cursor
            page_size: Results per page
            
        Returns:
            List of batch jobs with pagination
            
        Example:
            >>> # Get all running jobs
            >>> jobs = service.list_jobs(status="running")
            >>> for job in jobs.get("jobs", []):
            ...     print(f"{job['name']}: {job['status']}")
        """
        with APICallLogger(self.logger, "List Batch Jobs"):
            params = {"page_size": page_size}
            
            if status:
                params["status"] = status
            if cursor:
                params["cursor"] = cursor
            
            response = self._make_request(
                method="GET",
                endpoint=self.BATCH_CALLING_ENDPOINT,
                params=params
            )
            
            job_count = len(response.get("jobs", []))
            self.logger.info(f"Retrieved {job_count} batch jobs")
            return response
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a batch calling job.
        
        API Endpoint: POST /v1/convai/batch-calling/{job_id}/cancel
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            Cancellation confirmation
            
        Example:
            >>> service.cancel_job("batch_abc123")
        """
        with APICallLogger(self.logger, "Cancel Batch Job", job_id=job_id):
            response = self._make_request(
                method="POST",
                endpoint=f"{self.BATCH_CALLING_ENDPOINT}/{job_id}/cancel"
            )
            
            self.logger.info(f"Batch job cancelled: {job_id}")
            return response
    
    def get_job_calls(
        self,
        job_id: str,
        status: Optional[str] = None,
        cursor: Optional[str] = None,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get individual call results from a batch job.
        
        API Endpoint: GET /v1/convai/batch-calling/{job_id}/calls
        
        Args:
            job_id: Batch job identifier
            status: Filter by call status
            cursor: Pagination cursor
            page_size: Results per page
            
        Returns:
            List of individual call results with details
            
        Example:
            >>> calls = service.get_job_calls("batch_abc123")
            >>> for call in calls.get("calls", []):
            ...     print(f"{call['to_number']}: {call['status']}")
        """
        with APICallLogger(self.logger, "Get Batch Job Calls", job_id=job_id):
            params = {"page_size": page_size}
            
            if status:
                params["status"] = status
            if cursor:
                params["cursor"] = cursor
            
            response = self._make_request(
                method="GET",
                endpoint=f"{self.BATCH_CALLING_ENDPOINT}/{job_id}/calls",
                params=params
            )
            
            call_count = len(response.get("calls", []))
            self.logger.info(f"Retrieved {call_count} calls from batch job {job_id}")
            return response
