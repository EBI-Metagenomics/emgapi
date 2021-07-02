import json
from django.conf import settings
from rest_framework.reverse import reverse
from celery import Celery, group
import hashlib


def is_signature_valid(signature):
    if "molecule" not in signature or signature["molecule"].lower() != "dna":
        return False
    return True


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
    app = Celery('tasks', broker=settings.SOURMASH['celery_broker'], backend=settings.SOURMASH['celery_backend'])
    # r = app.send_task('tasks.run_gather', (name,))
    # return r.id
    job = group([
        app.signature(
            'tasks.run_gather',
            args=(names[name], name, mag_catalog),
        ) for name in names
    ], app=app)
    result = job.apply_async()
    result.save()
    return result.id


def get_sourmash_job_status(job_id, request):
    app = Celery('tasks', broker=settings.SOURMASH['celery_broker'], backend=settings.SOURMASH['celery_backend'])
    group_result = app.GroupResult.restore(job_id, app=app)
    signatures = []
    for result in group_result.results:
        signature = {
            "job_id": result.id,
            "status": result.status,
        }
        if result.status == 'SUCCESS':
            signature['result'] = result.result
            signature['results_url'] = reverse('genomes-results', args=[result.id], request=request)
        if result.status == 'FAILURE':
            signature['reason'] = str(result.result)

        signatures.append(signature)
    return {
        'group_id': job_id,
        'signatures': signatures
    }
    # r = app.AsyncResult(job_id)
    # response = {
    #     'job_id': job_id,
    #     'status': r.status
    # }
    # if r.status == 'SUCCESS':
    #     response['result'] = r.result
    # if r.status == 'FAILURE':
    #     response['reason'] = str(r.result)
    # return response


def get_result_file(job_id):
    path = f"{settings.SOURMASH['results_path']}/{job_id}.csv"
    return open(path, 'r')
