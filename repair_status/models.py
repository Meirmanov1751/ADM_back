from django.db import models

class Repair(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
    ]
    REPAIR_TYPES = [
        ('internal', 'Internal'),
        ('external', 'External'),
    ]

    name = models.CharField(max_length=255)
    region = models.CharField(max_length=255, verbose_name="Регион",blank=True, null=True)
    oblast = models.CharField(max_length=255, verbose_name="Область",blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    address = models.TextField(verbose_name="Адрес")
    mol = models.CharField(max_length=255, verbose_name="МОЛ", blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    repair_type = models.CharField(max_length=20, choices=REPAIR_TYPES)
    floor = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    budget = models.IntegerField(blank=True, null=True)
    mol = models.CharField(max_length=255,blank=True, null=True)
    budget_type = models.CharField(max_length=10, blank=True, null=True)

    @property
    def delay_reason(self):
        try:
            return self.repairdelayreason
        except RepairDelayReason.DoesNotExist:
            return None

    @property
    def progress(self):
        total_tasks = self.tasks.count()
        completed_tasks = self.tasks.filter(status='completed').count()
        return (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    @property
    def budget_progress(self):
        """Процент использованного бюджета на завершенные задачи относительно бюджета ремонта."""
        completed_task_budget = self.tasks.filter(status='completed').aggregate(
            total_budget=models.Sum('budget')
        )['total_budget'] or 0

        if self.budget is None or self.budget <= 0:
            return 0
        return (completed_task_budget / self.budget) * 100

    def __str__(self):
        return self.name

class RepairDelayReason(models.Model):
    repair = models.OneToOneField(Repair, on_delete=models.CASCADE, related_name='repairdelayreason')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delay Reason for {self.repair.name}"

class RepairDelayMedia(models.Model):
    delay_reason = models.ForeignKey(RepairDelayReason, related_name='media', on_delete=models.CASCADE)
    file = models.FileField(upload_to='repair_delay_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delay Media for {self.delay_reason}"

class RepairStartMedia(models.Model):
    repair = models.ForeignKey(Repair, related_name='start_media', on_delete=models.CASCADE)
    file = models.FileField(upload_to='repair_start_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Start file for {self.repair.name}"

class RepairCompletionMedia(models.Model):
    repair = models.ForeignKey(Repair, related_name='completion_media', on_delete=models.CASCADE)
    file = models.FileField(upload_to='repair_completion_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Completion file for {self.repair.name}"

class RepairTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    TASK_TYPES = [
        ('electrical', 'Electrical'),
        ('plumbing', 'Plumbing'),
        ('structural', 'Structural'),
        ('painting', 'Painting'),
    ]

    repair = models.ForeignKey(Repair, related_name='tasks', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    budget = models.IntegerField(blank=True, null=True)
    mol = models.CharField(max_length=255, blank=True, null=True)


    @property
    def delay_reason(self):
        try:
            return self.taskdelayreason
        except TaskDelayReason.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

class TaskDelayReason(models.Model):
    task = models.OneToOneField(RepairTask, on_delete=models.CASCADE, related_name='taskdelayreason')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delay Reason for {self.task.name}"

class TaskDelayMedia(models.Model):
    delay_reason = models.ForeignKey(TaskDelayReason, related_name='media', on_delete=models.CASCADE)
    file = models.FileField(upload_to='task_delay_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delay Media for {self.delay_reason}"

class RepairTaskMedia(models.Model):
    task = models.ForeignKey(RepairTask, related_name='media', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='repair_images/', blank=True, null=True)
    video = models.FileField(upload_to='repair_videos/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media for {self.task.name}"