# camunda.py
import httpx
import logging

CAMUNDA_BASE_URL = "http://localhost:8080/engine-rest"
PROCESS_KEY = "request_process"

logger = logging.getLogger(__name__)

def start_request_process(request_id):
    try:
        response = httpx.post(
            f"{CAMUNDA_BASE_URL}/process-definition/key/{PROCESS_KEY}/start",
            json={
                "variables": {
                    "requestId": {"value": request_id, "type": "Integer"}
                },
                "businessKey": str(request_id)
            }
        )
        response.raise_for_status()
        logger.info(f"Camunda process started for request {request_id}")
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to start Camunda process: {e}")
        return None

def complete_latest_task_by_request(request_id, status_value):
    try:
        response = httpx.get(
            f"{CAMUNDA_BASE_URL}/task?processInstanceBusinessKey={request_id}"
        )
        response.raise_for_status()
        tasks = response.json()
        if tasks:
            task_id = tasks[0]['id']
            return complete_task(task_id, {"status": {"value": status_value, "type": "String"}})
        else:
            logger.warning(f"No active tasks found for request {request_id}")
        return False
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch task for request {request_id}: {e}")
        return False

def complete_task(task_id, variables=None):
    try:
        data = {"variables": variables or {}}
        response = httpx.post(
            f"{CAMUNDA_BASE_URL}/task/{task_id}/complete",
            json=data
        )
        response.raise_for_status()
        logger.info(f"Completed task {task_id} with variables {variables}")
        return True
    except httpx.HTTPError as e:
        logger.error(f"Failed to complete Camunda task {task_id}: {e}")
        return False
