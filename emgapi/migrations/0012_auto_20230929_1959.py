# Generated by Django 3.2.18 on 2023-09-29 19:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0011_analysisjob_analysis_summary_json'),
    ]

    operations = [
        # migrations.SeparateDatabaseAndState(
        #     state_operations=[
        #         migrations.RenameField(
        #             model_name='analysisjob',
        #             old_name='analysis_summary_json',
        #             new_name='analysis_summary',
        #         ),
        #     ],
        # ),
        migrations.DeleteModel(
            name='AnalysisJobAnn',
        ),
    ]
