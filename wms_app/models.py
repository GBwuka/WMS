from django.db import models
from django.contrib.auth.models import User


class CurrentJob(models.Model):
    project_name = models.TextField()
    manager = models.CharField(max_length=150)
    month_job_content = models.TextField()
    key_task = models.TextField()
    key_task_html = models.TextField()
    first_week_job_content = models.TextField()
    second_week_job_content = models.TextField()
    third_week_job_content = models.TextField()
    forth_week_job_content = models.TextField()
    fifth_week_job_content = models.TextField()
    sixth_week_job_content = models.TextField()
    created_time = models.DateField()
    edit_flag = models.IntegerField(default=0)

    class Meta:
        db_table = 'current_job'

class TodoJob(models.Model):
    project_name = models.TextField()
    project_title = models.TextField()
    project_content = models.TextField()
    priority = models.IntegerField(default=0)
    manager = models.CharField(max_length=150)
    created_time = models.DateField()
    deadline_time = models.DateField()
    completed_time = models.DateField()
    status = models.IntegerField(default=0)
    remark = models.TextField()
    project_type = models.BooleanField(default=0)
    edit_flag = models.IntegerField(default=0)

    class Meta:
        db_table = 'todo_job'

class PainPoint(models.Model):
    project_name = models.TextField()
    project_title = models.TextField()
    project_content = models.TextField()
    manager = models.CharField(max_length=150)
    handler = models.CharField(max_length=150)
    created_time = models.DateField()
    project_type = models.BooleanField(default=0)
    plan = models.TextField()
    status = models.IntegerField(default=0)
    edit_flag = models.IntegerField(default=0)

    class Meta:
        db_table = 'pain_point'

class KPI(models.Model):
    kpi_name = models.TextField()
    kpi_content = models.TextField()
    created_time = models.DateField()
    edit_flag = models.IntegerField(default=0)

    class Meta:
        db_table = 'kpi'

class CurrentJobComment(models.Model):
    owner_username = models.CharField(max_length=150)
    target_username = models.CharField(max_length=150)
    content = models.TextField()
    created_time = models.CharField(max_length=20)
    parent_id = models.ForeignKey('CurrentJob')
    like_count = models.IntegerField(default=0)
    comment_id = models.IntegerField(default=0)

    class Meta:
        db_table = 'current_job_comment'

class TodoJobComment(models.Model):
    owner_username = models.CharField(max_length=150)
    target_username = models.CharField(max_length=150)
    content = models.TextField()
    created_time = models.CharField(max_length=20)
    parent_id = models.ForeignKey('TodoJob')
    like_count = models.IntegerField(default=0)
    comment_id = models.IntegerField(default=0)

    class Meta:
        db_table = 'todo_job_comment'

class PainPointComment(models.Model):
    owner_username = models.CharField(max_length=150)
    target_username = models.CharField(max_length=150)
    content = models.TextField()
    created_time = models.CharField(max_length=20)
    parent_id = models.ForeignKey('PainPoint')
    like_count = models.IntegerField(default=0)
    comment_id = models.IntegerField(default=0)

    class Meta:
        db_table = 'pain_point_comment'

class CommentList(models.Model):
    owner_username = models.CharField(max_length=150)
    target_username = models.CharField(max_length=150)
    created_time = models.CharField(max_length=20)
    read = models.BooleanField(default=0)
    comment_url = models.CharField(max_length=150)

    class Meta:
        db_table = 'comment_list'

class CurrentJobList(models.Model):
    project_name = models.TextField()
    manager = models.CharField(max_length=150)

    class Meta:
        db_table = 'current_job_list'