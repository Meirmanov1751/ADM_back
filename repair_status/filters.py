from django_filters import rest_framework as filters
from .models import Repair

class RepairFilter(filters.FilterSet):
    start_date = filters.DateFromToRangeFilter()
    end_date = filters.DateFromToRangeFilter()
    floor = filters.RangeFilter()
    repair_type = filters.MultipleChoiceFilter(
        choices=Repair.REPAIR_TYPES,
        null_label=None,  # Отключаем пустое значение как опцию
        method='filter_repair_type'  # Кастомный метод фильтрации
    )
    name = filters.CharFilter(lookup_expr='icontains')
    region = filters.CharFilter(lookup_expr='icontains')
    oblast = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    address = filters.CharFilter(lookup_expr='icontains')
    mol = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    address = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Repair
        fields = ['name','region','oblast','description','address','mol', 'description', 'address', 'start_date', 'end_date', 'repair_type', 'floor']

    def filter_repair_type(self, queryset, name, value):
        if value:  # Фильтруем только если есть непустое значение
            return queryset.filter(repair_type__in=value)
        return queryset  # Если пусто, не применяем фильтр