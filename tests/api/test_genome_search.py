import pytest
import io
import os
from django.conf import settings

from django.urls import reverse

from rest_framework import status
from celery import Celery

SIGNATURE_FILE_NAME = ""
MOCKED_JOB_ID = "MOCKED_JOB_ID"


def create_file_object(text):
    f = io.StringIO(text)
    f.name = SIGNATURE_FILE_NAME
    return f


def mock_get_celery_task(*args, **kwargs):
    obj = type('', (), {})()
    obj.id = "MOCKED_JOB_ID"
    obj.status = "SUCCESS"
    return obj


class TestStudyAPI:
    def test_genome_search_get(self, client):
        url = reverse("emgapi_v1:genomes-gather-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert type(rsp) == dict
        assert "data" in rsp
        assert "sourmash" in rsp["data"]

    def test_genome_search_post_with_non_valid_files(self, client):
        url = reverse("emgapi_v1:genomes-gather-list")
        data = {'file_uploaded': create_file_object('x')}
        with pytest.raises(Exception, match='Unable to parse the uploaded file'):
            client.post(url, data, format='multipart')
        data = {'file_uploaded': create_file_object('{"type": "a json that is not a signature"}')}
        with pytest.raises(Exception, match='Unable to parse the uploaded file'):
            client.post(url, data, format='multipart')

    def test_genome_search_post_with_valid_file(self, client, monkeypatch):
        monkeypatch.setattr(Celery, "send_task", mock_get_celery_task)
        url = reverse("emgapi_v1:genomes-gather-list")
        data = {'file_uploaded': create_file_object('{"molecule": "dna"}')}
        response = client.post(url, data, format='multipart')
        assert response.status_code == status.HTTP_200_OK
        # Checks that the signature file was created in the `signatures_path`
        assert os.path.exists(f"{settings.SOURMASH['signatures_path']}/{SIGNATURE_FILE_NAME}")
        rsp = response.json()
        assert "job_id" in rsp["data"]
        assert MOCKED_JOB_ID in rsp["data"]["job_id"]

    def test_genome_search_status(self, client, monkeypatch):
        monkeypatch.setattr(Celery, "AsyncResult", mock_get_celery_task)
        url = reverse("genomes-status", args=[MOCKED_JOB_ID])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert "job_id" in rsp["data"]
        assert MOCKED_JOB_ID == rsp["data"]["job_id"]
        assert "SUCCESS" == rsp["data"]["status"]

    def test_genome_search_get_result(self, client, monkeypatch):
        monkeypatch.setattr(Celery, "AsyncResult", mock_get_celery_task)
        url = reverse("genomes-results", args=[MOCKED_JOB_ID])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.headers['Content-Type'] == "text/csv"
        lines = response.content.decode('utf8').split('\n')
        assert len(lines) > 1
        assert "intersect_bp" in lines[0]
