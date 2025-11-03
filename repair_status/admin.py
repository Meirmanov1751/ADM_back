from django.contrib import admin
from .models import Repair, RepairTask, RepairStartMedia, RepairCompletionMedia, RepairDelayReason, RepairDelayMedia, TaskDelayReason, TaskDelayMedia, RepairTaskMedia

@admin.register(Repair)
class RepairAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'repair_type']
    search_fields = ['name', 'address']

@admin.register(RepairTask)
class RepairTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'repair', 'status', 'due_date']
    list_filter = ['status', 'task_type']
    search_fields = ['name']

admin.site.register(RepairStartMedia)
admin.site.register(RepairCompletionMedia)
admin.site.register(RepairDelayReason)
admin.site.register(RepairDelayMedia)
admin.site.register(TaskDelayReason)
admin.site.register(TaskDelayMedia)
admin.site.register(RepairTaskMedia)