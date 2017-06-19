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
    r'studies',
    views.StudyViewSet,
    base_name='studies'
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

# pub_router = NestedSimpleRouter(router, r'studies', lookup='studies')
# pub_router.register(
#     r'publications',
#     views.StudyPublicationViewSet,
#     base_name='studies-publications')
#
# sample_router = NestedSimpleRouter(router, r'studies', lookup='studies')
# sample_router.register(
#     r'samples',
#     views.StudySampleViewSet,
#     base_name='studies-samples')


urlpatterns = router.urls
# urlpatterns = [
#     url(r'^', include(router.urls)),
#     url(r'^', include(pub_router.urls)),
#     url(r'^', include(sample_router.urls)),
# ]
