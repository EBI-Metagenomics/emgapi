from rest_framework import mixins

from rest_framework_mongoengine.viewsets import GenericViewSet

from emgapi import mixins as emg_mixins


class ReadOnlyModelViewSet(mixins.RetrieveModelMixin,
                           emg_mixins.ListModelMixin,
                           GenericViewSet):
    """ Adaptation of DRF ReadOnlyModelViewSet """
    pass


class MultipleFieldLookupModelViewSet(emg_mixins.MultipleFieldLookupMixin,
                                      emg_mixins.ListModelMixin,
                                      GenericViewSet):
    """ Adaptation of DRF ReadOnlyModelViewSet """
    pass


class ListReadOnlyModelViewSet(emg_mixins.ListModelMixin,
                               GenericViewSet):
    """ Adaptation of DRF ReadOnlyModelViewSet """
    pass
