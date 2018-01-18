"""wms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf import settings

from wms_app import views, func_utils

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/$', views.login),

    url(r'^wms/woshihoumen/$', func_utils.reset_password),

    url(r'^$', views.homepage),
    url(r'^wms/login/$', views.login),
    url(r'^wms/logout/$', views.logout),
    url(r'^wms/month_job/$', views.month_job),
    url(r'^wms/add_month_job/$', views.add_month_job),
    url(r'^wms/edit_month_job/$', views.edit_month_job),
    url(r'^wms/edit_key_task_job/$', views.edit_key_task_job),
    url(r'^wms/todo_job/$', views.todo_job),
    url(r'^wms/add_todo_job/$', views.add_todo_job),
    url(r'^wms/edit_todo_job/$', views.edit_todo_job),
    url(r'^wms/pain_point/$', views.pain_point),
    url(r'^wms/add_pain_point/$', views.add_pain_point),
    url(r'^wms/edit_pain_point/$', views.edit_pain_point),
    url(r'^wms/kpi/$', views.kpi),
    url(r'^wms/add_kpi/$', views.add_kpi),
    url(r'^wms/edit_kpi/$', views.edit_kpi),
    url(r'^wms/key_task_timeline/$', views.key_task_timeline),
    url(r'^wms/comment_list/$', views.comment_list),
    url(r'^wms/default_project/$', views.default_project),

    url(r'^wms/upload/(?P<dir_name>[^/]+)$', func_utils.upload_image),
    url(r'^wms/excel_export/$', func_utils.excel_export),
]
