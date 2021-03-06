# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-09-04 02:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CommentList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner_username', models.CharField(max_length=150)),
                ('created_time', models.CharField(max_length=20)),
                ('read', models.BooleanField(default=0)),
                ('comment_url', models.CharField(max_length=150)),
            ],
            options={
                'db_table': 'comment_list',
            },
        ),
        migrations.CreateModel(
            name='CurrentJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_name', models.TextField()),
                ('manager', models.CharField(max_length=150)),
                ('month_job_content', models.TextField()),
                ('key_task', models.TextField()),
                ('key_task_html', models.TextField()),
                ('first_week_job_content', models.TextField()),
                ('second_week_job_content', models.TextField()),
                ('third_week_job_content', models.TextField()),
                ('forth_week_job_content', models.TextField()),
                ('fifth_week_job_content', models.TextField()),
                ('sixth_week_job_content', models.TextField()),
                ('created_time', models.DateField()),
                ('edit_flag', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'current_job',
            },
        ),
        migrations.CreateModel(
            name='CurrentJobComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner_username', models.CharField(max_length=150)),
                ('target_username', models.CharField(max_length=150)),
                ('content', models.TextField()),
                ('created_time', models.CharField(max_length=20)),
                ('like_count', models.IntegerField(default=0)),
                ('comment_id', models.IntegerField(default=0)),
                ('parent_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wms_app.CurrentJob')),
            ],
            options={
                'db_table': 'current_job_comment',
            },
        ),
        migrations.CreateModel(
            name='CurrentJobList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_name', models.TextField()),
                ('manager', models.CharField(max_length=150)),
            ],
            options={
                'db_table': 'current_job_list',
            },
        ),
        migrations.CreateModel(
            name='KPI',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kpi_name', models.TextField()),
                ('kpi_content', models.TextField()),
                ('created_time', models.DateField()),
                ('edit_flag', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'kpi',
            },
        ),
        migrations.CreateModel(
            name='PainPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_name', models.TextField()),
                ('project_title', models.TextField()),
                ('project_content', models.TextField()),
                ('manager', models.CharField(max_length=150)),
                ('handler', models.CharField(max_length=150)),
                ('created_time', models.DateField()),
                ('project_type', models.BooleanField(default=0)),
                ('plan', models.TextField()),
                ('status', models.IntegerField(default=0)),
                ('edit_flag', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'pain_point',
            },
        ),
        migrations.CreateModel(
            name='PainPointComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner_username', models.CharField(max_length=150)),
                ('target_username', models.CharField(max_length=150)),
                ('content', models.TextField()),
                ('created_time', models.CharField(max_length=20)),
                ('like_count', models.IntegerField(default=0)),
                ('comment_id', models.IntegerField(default=0)),
                ('parent_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wms_app.PainPoint')),
            ],
            options={
                'db_table': 'pain_point_comment',
            },
        ),
        migrations.CreateModel(
            name='TodoJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_name', models.TextField()),
                ('project_title', models.TextField()),
                ('project_content', models.TextField()),
                ('priority', models.IntegerField(default=0)),
                ('manager', models.CharField(max_length=150)),
                ('created_time', models.DateField()),
                ('deadline_time', models.DateField()),
                ('completed_time', models.DateField()),
                ('status', models.IntegerField(default=0)),
                ('remark', models.TextField()),
                ('project_type', models.BooleanField(default=0)),
                ('edit_flag', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'todo_job',
            },
        ),
        migrations.CreateModel(
            name='TodoJobComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner_username', models.CharField(max_length=150)),
                ('target_username', models.CharField(max_length=150)),
                ('content', models.TextField()),
                ('created_time', models.CharField(max_length=20)),
                ('like_count', models.IntegerField(default=0)),
                ('comment_id', models.IntegerField(default=0)),
                ('parent_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wms_app.TodoJob')),
            ],
            options={
                'db_table': 'todo_job_comment',
            },
        ),
    ]
