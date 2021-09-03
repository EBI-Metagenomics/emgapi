import json
import tarfile
import hashlib
import os.path

from django.conf import settings
from rest_framework.reverse import reverse
from celery import Celery, group
from celery.app.control import Control



def is_signature_valid(signature):
    if "molecule" not in signature or signature["molecule"].lower() != "dna":
        return False
    return True


app = Celery('tasks', broker=settings.SOURMASH['celery_broker'], backend=settings.SOURMASH['celery_backend'])
app.conf.update(
    result_extended=True
)
control = Control(app=app)


def validate_sourmash_signature(json_str):
    signature = json.loads(json_str)
    if type(signature) == list:
        for s in signature:
            if is_signature_valid(s):
                continue
            elif 'signatures' in s:
                for ss in s['signatures']:
                    if is_signature_valid(ss):
                        continue
                    else:
                        raise Exception("One of the signatures in the uploaded file is not valid")
            else:
                raise Exception("One of the signatures in the uploaded file is not valid")
    elif not is_signature_valid(signature):
        raise Exception("The file is not a valid sourmash signature")


def get_unique_name(file):
    md5_hash = hashlib.md5()
    for chunk in file.chunks():
        md5_hash.update(chunk)
    return f"{md5_hash.hexdigest()}.sig"


def save_signature(file):
    name = get_unique_name(file)
    path = f"{settings.SOURMASH['signatures_path']}/{name}"
    with open(path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return name


def send_sourmash_jobs(names, mag_catalog):
    job = group([
        app.signature(
            'tasks.run_gather',
            args=(names[name], name, mag_catalog),
        ) for name in names
    ], app=app)
    result = job.apply_async()
    result.save()
    try:
        children_ids = {
            r.args[1]: r.id
            for r in result.results
        }
    except Exception:
        children_ids = None
    return result.id, children_ids


# Assumes there is only one worker in the queue
def get_task_pos_in_reserved(task_id, reserved):
    pos = 0
    for tasks in reserved.values():
        for task in tasks:
            if task["id"] == task_id:
                return pos + 1
            pos += 1
    return None


def get_task_worker_status(task_id, inspect):
    tasks_by_worker = inspect.query_task(task_id)
    for task in tasks_by_worker.values():
        status = task[task_id][0]
        if status == 'reserved':
            return "IN_QUEUE"
        if status == 'active':
            return "RUNNING"


def get_sourmash_job_status(job_id, request):
    inspect = control.inspect()
    ping = inspect.ping()
    reserved = None
    group_result = app.GroupResult.restore(job_id, app=app)
    if group_result is None:
        return None
    signatures = []
    has_results = False
    for result in group_result.results:
        signature = {
            "job_id": result.id,
            "status": result.status,
        }
        try:
            signature['filename'] = result.args[1]
        except Exception:
            pass
        if result.status == 'SUCCESS':
            signature['result'] = result.result
            signature['results_url'] = reverse('genomes-results', args=[result.id], request=request)
            has_results = True
        elif result.status == 'FAILURE':
            signature['reason'] = str(result.result)
        elif result.status == 'PENDING' and ping is not None:
            signature["status"] = get_task_worker_status(result.id, inspect)
            if signature["status"] == "IN_QUEUE":
                if reserved is None:
                    reserved = inspect.reserved()
                signature['position_in_queue'] = get_task_pos_in_reserved(result.id, reserved)

        signatures.append(signature)
    return {
        'group_id': job_id,
        'signatures': signatures,
        'results_url': reverse('genomes-results', args=[job_id], request=request) if has_results else None,
        'worker_status': "OFFLINE" if ping is None else "OK"
    }

def generate_tgz_from_group_id(group_id):
    group_result = app.GroupResult.restore(group_id, app=app)
    if group_result is None:
        return None
    tar = tarfile.open(f"{settings.SOURMASH['results_path']}/{group_id}.tgz", "w:gz")
    for result in group_result.results:
        if result.status == "SUCCESS":
            tar.add(
                f"{settings.SOURMASH['results_path']}/{result.id}.csv",
                arcname=f"{result.id}.csv",
            )
    tar.close()

def get_result_file(job_id):
    path = f"{settings.SOURMASH['results_path']}/{job_id}.csv"
    try:
        return open(path, 'r'), 'text/csv'
    except FileNotFoundError:
        gzpath = f"{settings.SOURMASH['results_path']}/{job_id}.tgz"
        try:
            return open(gzpath, 'rb'), 'application/gzip'
        except FileNotFoundError:
            generate_tgz_from_group_id(job_id)
            try:
                return open(gzpath, 'rb'), 'application/gzip'
            except FileNotFoundError:
                return None, None


