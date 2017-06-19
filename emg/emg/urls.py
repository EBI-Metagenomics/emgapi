# -*- coding: utf-8 -*-

from django.conf.urls import include, url

from rest_framework.schemas import get_schema_view
from rest_framework.renderers import CoreJSONRenderer

from rest_framework_swagger.views import get_swagger_view


schema_view = get_schema_view(
    title='EBI metagenomics API',
    renderer_classes=[CoreJSONRenderer]
)

docs_schema_view = get_swagger_view(title='EBI metagenomics API')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [

    # url(r'^admin/', admin.site.urls),

    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

    url(r'^api/', include('emg_api.urls')),

    url(r'^schema/$', schema_view),

    url(r'^docs/$', docs_schema_view),

]
