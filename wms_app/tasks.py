from celery import task
from django.conf import settings
from email.mime.image import MIMEImage
from django.core import mail
from PIL import Image
from datetime import datetime
import logging

from .models import TodoJob, CurrentJobList, CurrentJob

logger = logging.getLogger('wms.wms_app.views')

@task()
def send_mail(to_mail, mail_type, content):
    remarks = ""
    if mail_type == 'assign_new':
        title = "您收到一个新痛点任务，请登录平台查看"
    elif mail_type == 'assign_old':
        title = "您不再参与一个痛点任务，请登录平台查看"
    elif mail_type == 'apply':
        title = "您创建的痛点任务被领取，请登录平台查看"
    remarks += "平台链接：<a href='http://124.93.223.118:65534/'>http://124.93.223.118:65534/</a><br/><br/>\
        <strong><font color='blue'>本邮件由系统自动发送</font></strong><br/>"
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Title</title>
    </head>
    <body>
    <strong><font color='red'>''' + title + '''</font></strong><br/>
    <br/>''' + content + '''<br/><br/>
    备注说明：<br/>''' + remarks + '''
    </body>
    </html>
    '''
    msg = mail.EmailMessage(title, html, settings.EMAIL_HOST_USER, to_mail)
    msg.content_subtype = 'html'
    msg.encoding = 'utf-8'
    msg.send()

@task()
def check_todojob():
    now = datetime.now().strftime("%Y-%m-%d")
    data = TodoJob.objects.filter(status=1).values('project_name', 'project_title', 'manager', 'deadline_time', 'project_type')
    for d in data:
        remarks = ""
        if d['deadline_time'].strftime("%Y-%m-%d") == now:
            to_mail = []
            if d['manager'] == 'sawyer':
                to_mail.append('sawyersun@21kunpeng.com')
            else:
                to_mail.append(d['manager']+'@21kunpeng.com')
            if d['project_type'] == 0:
                project_type = '公共类'
            else:
                project_type = '项目单独'
            content = '项目名称：' + str(d['project_name']) + ' ' + '标题：' + str(d['project_title']) + ' ' + '截止时间：' +\
                str(d['deadline_time'].strftime("%Y-%m-%d")) + ' ' + '类型：' + str(project_type)
            remarks += "平台链接：<a href='http://124.93.223.118:65534/'>http://124.93.223.118:65534/</a><br/><br/>\
                <strong><font color='blue'>本邮件由系统自动发送</font></strong><br/>"
            html = '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Title</title>
            </head>
            <body>
            <strong><font color='red'>您有一个待跟进工作即将到期，请登录平台查看</font></strong><br/>
            <br/>''' + content + '''<br/><br/>
            备注说明：<br/>''' + remarks + '''
            </body>
            </html>
            '''
            msg = mail.EmailMessage("您有一个待跟进工作即将到期，请登录平台查看", html, settings.EMAIL_HOST_USER, to_mail)
            msg.content_subtype = 'html'
            msg.encoding = 'utf-8'
            msg.send()

@task()
def add_default_project():
    now = datetime.now().strftime("%Y-%m-%d")
    data = CurrentJobList.objects.values('id', 'project_name', 'manager')
    for d in data:
        CurrentJob.objects.create(project_name=d['project_name'], manager=d['manager'], created_time=now)
        logger.info("celery_task-create-CurrentJob(" + str(d['project_name']) + "," + str(d['manager']) + "," + str(now) + ")")