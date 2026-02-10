from mongoengine.base import EmbeddedDocumentList
from rest_framework.filters import OrderingFilter


class MongoOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset: EmbeddedDocumentList, view):
        """
        EmbeddedDocumentList isn't a queryset so can't be `order_by()`ed.
        Use native python sort instead.
        :param request:
        :param queryset:
        :param view:
        :return:
        """
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset
        # ignores compound ordering
        field = ordering[0].lstrip('-')
        reverse = ordering[0].startswith('-')
        return sorted(queryset, key=lambda row: getattr(row, field), reverse=reverse)
