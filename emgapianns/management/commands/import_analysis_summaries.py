from django.core.management.base import BaseCommand
from emgapi.models import AnalysisJob


class Command(BaseCommand):
    help = 'Copy values from analysis_summary to analysis_summary_json for a specified batch of AnalysisJob records'

    def add_arguments(self, parser):
        parser.add_argument('batch_number', type=int, help='Batch number to process')

    def handle(self, *args, **options):
        batch_number = options['batch_number']
        batch_size = 10000

        try:
            start_index = (batch_number - 1) * batch_size
            end_index = batch_number * batch_size

            analysis_jobs = AnalysisJob.objects.all()[start_index:end_index]

            self.stdout.write(self.style.SUCCESS(f'Processing batch {batch_number} of {len(analysis_jobs)} records.'))

            updated_records = []

            for analysis_job in analysis_jobs:
                analysis_summary = analysis_job.analysis_summary
                if analysis_summary:
                    analysis_job.analysis_summary_json = analysis_summary
                    updated_records.append(analysis_job)

            if updated_records:
                AnalysisJob.objects.bulk_update(updated_records, ['analysis_summary_json'])

            self.stdout.write(self.style.SUCCESS(f'Values copied successfully for batch {batch_number}.'))
        except AnalysisJob.DoesNotExist:
            self.stdout.write(self.style.ERROR('AnalysisJob table does not exist or is empty.'))
