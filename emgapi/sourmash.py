import json
from django.conf import settings
from celery import Celery


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


def get_unique_name(name):
    # TODO: add a unique number to avoid overwritting files
    return name


def save_signature(file):
    name = get_unique_name(file.name)
    path = f"{settings.SOURMASH['signatures_path']}/{name}"
    with open(path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return name


def send_sourmash_job(name):
    app = Celery('tasks', broker=settings.SOURMASH['celery_broker'], backend=settings.SOURMASH['celery_backend'])
    r = app.send_task('tasks.run_gather', (name,))
    return r.id


def get_sourmash_job_satus(job_id):
    app = Celery('tasks', broker=settings.SOURMASH['celery_broker'], backend=settings.SOURMASH['celery_backend'])
    r = app.AsyncResult(job_id)
    response = {
        'job_id': job_id,
        'status': r.status
    }
    if r.status == 'FAILURE':
        response['reason'] = str(r.result)
    return response


def get_result_file(job_id):
    path = f"{settings.SOURMASH['results_path']}/{job_id}.csv"
    return open(path, 'r')
