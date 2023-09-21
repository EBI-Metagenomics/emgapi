from django.core.management.base import BaseCommand
from emgapi.models import AnalysisJob


class Command(BaseCommand):
    help = 'Copy values from analysis_summary to analysis_summary_json for a specified batch of AnalysisJob records'

    def handle(self, *args, **options):
        batch_size = 10000
        batch_number = 1
        total_updated_records = 0

        total_no_of_analysis_jobs = AnalysisJob.objects.count()
        self.stdout.write(f'Total AnalysisJob records: {total_no_of_analysis_jobs}')

        while True:
            start_index = (batch_number - 1) * batch_size
            end_index = batch_number * batch_size

            analysis_jobs = AnalysisJob.objects.all()[start_index:end_index]

            if not analysis_jobs:
                break

            self.stdout.write(self.style.SUCCESS(f'Processing batch {batch_number} of {len(analysis_jobs)} records.'))

            updated_records = []

            for analysis_job in analysis_jobs:
                analysis_summary = analysis_job.analysis_summary
                if analysis_summary and not analysis_job.analysis_summary_json:
                    analysis_job.analysis_summary_json = analysis_summary
                    updated_records.append(analysis_job)

            if updated_records:
                AnalysisJob.objects.bulk_update(updated_records, ['analysis_summary_json'])
                total_updated_records += len(updated_records)

            self.stdout.write(f'Updated records so far: {total_updated_records}/{total_no_of_analysis_jobs}')

            self.stdout.write(self.style.SUCCESS(f'Values copied successfully for batch {batch_number}.'))
            self.stdout.write(self.style.SUCCESS(f'Updated {len(updated_records)} records.'))

            batch_number += 1
