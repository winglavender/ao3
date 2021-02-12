from server import q
from rq.registry import FailedJobRegistry

registry = FailedJobRegistry(queue=q)
for job_id in registry.get_job_ids():
    registry.remove(job_id)

