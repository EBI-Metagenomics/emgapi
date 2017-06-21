# -*- coding: utf-8 -*-

from emg_api import views

from rest_framework.routers import DefaultRouter
# from rest_framework_nested.routers import NestedSimpleRouter

urlpatterns = []

router = DefaultRouter()

router.register(
    r'biome',
    views.BiomeHierarchyTreeViewSet,
    base_name='biome'
)

router.register(
    r'projects',
    views.ProjectViewSet,
    base_name='projects'
)

router.register(
    r'samples',
    views.SampleViewSet,
    base_name='samples'
)

router.register(
    r'jobs',
    views.AnalysisJobViewSet,
    base_name='jobs'
)

router.register(
    r'pipelines',
    views.PipelineReleaseViewSet,
    base_name='pipelines'
)

router.register(
    r'publications',
    views.PublicationViewSet,
    base_name='publications'
)

urlpatterns = router.urls
