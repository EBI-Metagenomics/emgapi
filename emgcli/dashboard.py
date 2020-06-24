from django.utils.translation import ugettext_lazy as _

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name


class MgnifyDashboard(Dashboard):
    """
    Mgnify index dashboard for www.
    """

    def init_with_context(self, context):
        site_name = get_admin_site_name(context)

        # col 1
        self.children.append(modules.ModelList(
            _('Users'),
            column=1,
            collapsible=False,
            models=('django.contrib.*',)
        ))

        self.children.append(modules.ModelList(
            _('Genomes'),
            column=1,
            collapsible=False,
            models=(
                'emgapi.models.Genome',
                'emgapi.models.GenomeDownload',
                'emgapi.models.GenomeSet',
                'emgapi.models.Release',
                'emgapi.models.ReleaseDownload',
                'emgapi.models.GeographicLocation'
            ),
        ))

        self.children.append(modules.ModelList(
            _('Common'),
            column=1,
            collapsible=False,
            models=(
                'emgapi.models.Biome',
                'emgapi.models.FileFormat',
                'emgapi.models.VariableNames',
            ),
        ))

        self.children.append(modules.ModelList(
            _('Categories'),
            column=1,
            collapsible=False,
            models=(
                'emgapi.models.CogCat',
                'emgapi.models.KeggModule',
                'emgapi.models.KeggClass',
                'emgapi.models.AntiSmashGC',
            ),
        ))

        # col 2
        self.children.append(modules.ModelList(
            _('Entities'),
            column=2,
            collapsible=False,
            models=(
                'emgapi.models.Sample',
                'emgapi.models.Run',
                'emgapi.models.Assembly',
                'emgapi.models.Study',
                'emgapi.models.StudyErrorType',
                'emgapi.models.BlacklistedStudyAdmin',
            ),
        ))

        self.children.append(modules.ModelList(
            _('Analysis'),
            column=2,
            collapsible=False,
            models=(
                'emgapi.models.AnalysisJob',
                'emgapi.models.AnalysisJobAnn',
                'emgapi.models.SampleAnn',
                'emgapi.models.AnalysisJobDownload',
                'emgapi.models.AnalysisMetadataVariableNames',
            ),
        ))

        self.children.append(modules.ModelList(
            _('Pipeline'),
            column=2,
            collapsible=False,
            models=(
                'emgapi.models.Pipeline',
                'emgapi.models.PipelineTool',
            ),
        ))

        # col 3
        self.children.append(modules.ModelList(
            _('Publications'),
            column=3,
            collapsible=False,
            models=(
                'emgapi.models.Publication',
            ),
        ))

        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            limit=5,
            collapsible=False,
            column=3,
        ))
