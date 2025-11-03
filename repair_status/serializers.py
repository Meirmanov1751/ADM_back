from rest_framework import serializers
from .models import RepairTask, RepairTaskMedia, Repair, RepairDelayReason, RepairStartMedia, RepairCompletionMedia, TaskDelayReason, RepairDelayMedia, TaskDelayMedia

class RepairTaskMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairTaskMedia
        fields = ['id', 'image', 'video', 'uploaded_at']

class TaskDelayMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDelayMedia
        fields = ['id', 'file', 'uploaded_at']

class TaskDelayReasonSerializer(serializers.ModelSerializer):
    media = TaskDelayMediaSerializer(many=True, read_only=True)
    delay_files = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)

    class Meta:
        model = TaskDelayReason
        fields = ['id', 'reason', 'created_at', 'media', 'delay_files']

    def create(self, validated_data):
        delay_files = validated_data.pop('delay_files', [])
        delay_reason = TaskDelayReason.objects.create(**validated_data)
        for file in delay_files:
            TaskDelayMedia.objects.create(delay_reason=delay_reason, file=file)
        return delay_reason

class RepairTaskSerializer(serializers.ModelSerializer):
    media = RepairTaskMediaSerializer(many=True, read_only=True)
    delay_reason = TaskDelayReasonSerializer(source='taskdelayreason', read_only=True)
    media_files = serializers.ListField(child=serializers.ImageField(), required=False, write_only=True)

    class Meta:
        model = RepairTask
        fields = ['id', 'mol','repair', 'name', 'status', 'due_date', 'description', 'task_type', 'media', 'media_files', 'delay_reason']

    def update(self, instance, validated_data):
        media_files = self.context['request'].FILES.getlist('media_files')
        instance.status = validated_data.get('status', instance.status)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        for media in media_files:
            RepairTaskMedia.objects.create(task=instance, image=media)
        return instance

class RepairDelayMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairDelayMedia
        fields = ['id', 'file', 'uploaded_at']

class RepairDelayReasonSerializer(serializers.ModelSerializer):
    media = RepairDelayMediaSerializer(many=True, read_only=True)
    delay_files = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)

    class Meta:
        model = RepairDelayReason
        fields = ['id', 'reason', 'created_at', 'media', 'delay_files']

    def create(self, validated_data):
        delay_files = validated_data.pop('delay_files', [])
        delay_reason = RepairDelayReason.objects.create(**validated_data)
        for file in delay_files:
            RepairDelayMedia.objects.create(delay_reason=delay_reason, file=file)
        return delay_reason

class RepairStartMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairStartMedia
        fields = ['id', 'file', 'uploaded_at']

class RepairCompletionMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairCompletionMedia
        fields = ['id', 'file', 'uploaded_at']

class RepairSerializer(serializers.ModelSerializer):
    tasks = RepairTaskSerializer(many=True, read_only=True)
    delay_reason = RepairDelayReasonSerializer(source='repairdelayreason', read_only=True)
    start_media = RepairStartMediaSerializer(many=True, read_only=True)
    completion_media = RepairCompletionMediaSerializer(many=True, read_only=True)
    progress = serializers.ReadOnlyField()
    budget_progress = serializers.ReadOnlyField()
    start_files = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)
    completion_files = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)

    class Meta:
        model = Repair
        fields = [
            'id', 'name','budget_type','budget','mol','region','oblast','description','address','mol','budget_progress', 'description', 'address', 'start_date', 'end_date', 'repair_type', 'floor', 'status',
            'created_at', 'progress', 'tasks', 'delay_reason', 'start_media', 'completion_media', 'start_files', 'completion_files'
        ]

    def create(self, validated_data):
        start_files = validated_data.pop('start_files', [])
        repair = Repair.objects.create(**validated_data)
        for file in start_files:
            RepairStartMedia.objects.create(repair=repair, file=file)
        return repair

    def update(self, instance, validated_data):
        start_files = self.context['request'].FILES.getlist('start_files')
        completion_files = self.context['request'].FILES.getlist('completion_files')
        instance.status = validated_data.get('status', instance.status)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        for file in start_files:
            RepairStartMedia.objects.create(repair=instance, file=file)
        for file in completion_files:
            RepairCompletionMedia.objects.create(repair=instance, file=file)
        return instance