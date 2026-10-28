import django_filters

from .models import Event


class EventFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact")
    start_after = django_filters.IsoDateTimeFilter(field_name="start_at", lookup_expr="gte")
    start_before = django_filters.IsoDateTimeFilter(field_name="start_at", lookup_expr="lte")
    min_price = django_filters.NumberFilter(field_name="ticket_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="ticket_price", lookup_expr="lte")
    free = django_filters.BooleanFilter(method="filter_free")

    class Meta:
        model = Event
        fields = []

    def filter_free(self, queryset, name, value):
        return queryset.filter(ticket_price=0) if value else queryset