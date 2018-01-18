import os
import json
import uuid
import xlwt
import logging

from io import StringIO, BytesIO
from datetime import datetime
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib import auth
from django.db.models import Avg, Max, Min, Count, Sum
from django.conf import settings

from .models import CurrentJob, TodoJob, PainPoint, KPI, CurrentJobComment, TodoJobComment, PainPointComment, CommentList, CurrentJobList
from .tasks import send_mail

logger = logging.getLogger('wms.wms_app.func_utils')

#kindeditor定制化配置，上传路径，工具栏
kindeditor_style = {
    'resizeType': 1,
    'uploadJson': '/wms/upload/kindeditor',
    'items': [
        'undo', 'redo', '|', 'cut', 'copy', 'paste',
        'plainpaste', 'wordpaste', '|', 'justifyleft', 'justifycenter', 'justifyright',
        'justifyfull', 'insertorderedlist', 'insertunorderedlist', 'indent', 'outdent', 'subscript',
        'superscript', 'selectall', '|', 'fullscreen', 'preview', '/',
        'formatblock', 'fontname', 'fontsize', '|', 'forecolor', 'hilitecolor', 'bold',
        'italic', 'underline', 'strikethrough', 'lineheight', 'removeformat', '|', 'image', 'insertfile', 'link', 'unlink',
        'table', 'hr', 'emoticons'
    ]
}

kindeditor_comment_style = {
    'resizeType': 0,
    'uploadJson': '/wms/upload/kindeditor',
    'items': ['justifyleft', 'justifycenter', 'justifyright',
        'justifyfull', 'insertorderedlist', 'insertunorderedlist', '|', 
        'formatblock', 'fontname', 'fontsize', '|', 'forecolor', 'hilitecolor', 'bold',
        'italic', 'underline', '|', 'table', 'emoticons']
}

kindeditor_empty_style = {
    'resizeType': 0,
    'items': []
}

@csrf_exempt
def upload_image(request, dir_name):
    result = {'error':1,'message':'上传出错'}
    files = request.FILES.get('imgFile', None)
    if files:
        result = image_upload(files, dir_name, request.user.username)
    return HttpResponse(json.dumps(result), content_type='application/json')

#目录创建
def upload_generation_dir(dir_name, username):
    today = datetime.today()
    dir_name = dir_name + '/%s/%d/%d/' %(username, today.year, today.month)
    # if not os.path.exists(settings.MEDIA_ROOT + dir_name):
    #     os.makedirs(settings.MEDIA_ROOT + dir_name)
    return dir_name

#文件上传
def image_upload(files, dir_name, username):
    #允许上传的类型
    allow_suffix = ['jpg','png','jpeg','git','bmp','JPG','PNG','JPEG','GIT','BMP','txt','TXT','zip','ZIP','rar','RAR','7z','7Z',
        'doc','docx','DOC','DOCX','ppt','pptx','PPT','PPTX','xls','xlsx','XLS','XLSX','pdf','PDF']
    file_suffix = files.name.split('.')[-1]
    if file_suffix not in allow_suffix:
        return {'error':1,'message':'文件格式不正确'}
    relative_path_file = upload_generation_dir(dir_name, username)
    path = os.path.join(settings.MEDIA_ROOT, relative_path_file)
    if not os.path.exists(path):
        os.makedirs(path)
    # file_name = str(uuid.uuid1()) + '.' + file_suffix
    # path_file = os.path.join(path, file_name)
    path_file = os.path.join(path, files.name)
    file_url = settings.MEDIA_URL + relative_path_file + files.name
    open(path_file,'wb').write(files.file.read())
    return {'error':0,'url':file_url}

#导出excel
def excel_export(request):
    wb = xlwt.Workbook(encoding='utf-8')
    modal = request.GET.get('modal')

    style_heading = xlwt.easyxf("""
        font:
            name Arial,
            colour_index white,
            bold on,
            height 0xA0;
        align:
            wrap off,
            vert center,
            horiz center;
        pattern:
            pattern solid,
            fore-colour 0x19;
        borders:
            left THIN,
            right THIN,
            top THIN,
            bottom THIN;
        """
                                )
    style_body = xlwt.easyxf("""
        font:
            name Arial,
            bold off,
            height 0XA0;
        align:
            wrap on,
            vert center,
            horiz left;
        borders:
            left THIN,
            right THIN,
            top THIN,
            bottom THIN;
        """
                             )
    style_green = xlwt.easyxf(" pattern: pattern solid,fore-colour 0x11;")
    style_red = xlwt.easyxf(" pattern: pattern solid,fore-colour 0x0A;")
    fmts = [
        'M/D/YY',
        'D-MMM-YY',
        'D-MMM',
        'MMM-YY',
        'h:mm AM/PM',
        'h:mm:ss AM/PM',
        'h:mm',
        'h:mm:ss',
        'M/D/YY h:mm',
        'mm:ss',
        '[h]:mm:ss',
        'mm:ss.0',
    ]

    style_body.num_format_str = fmts[0]
    if modal == 'month_job':
        sheet_name = u'工作统计'
        sheet_first = wb.add_sheet(sheet_name)
        sheet_first.write(0, 0, u'项目', style_heading)
        sheet_first.write(0, 1, u'负责人', style_heading)
        sheet_first.write(0, 2, u'创建时间', style_heading)
        row = 1
        contents = CurrentJob.objects.values('project_name', 'manager', 'created_time')
        for content in contents:
            sheet_first.write(row, 0, content['project_name'], style_body)
            sheet_first.write(row, 1, content['manager'], style_body)
            sheet_first.write(row, 2, content['created_time'].strftime('%Y-%m-%d'), style_body)

            # 第一行加宽
            sheet_first.col(0).width = 100 * 50
            sheet_first.col(1).width = 50 * 50
            sheet_first.col(2).width = 50 * 50
            row += 1
    elif modal == 'todo_job':
        sheet_name = u'待跟进工作'
        sheet_first = wb.add_sheet(sheet_name)
        sheet_first.write(0, 0, u'项目', style_heading)
        sheet_first.write(0, 1, u'标题', style_heading)
        sheet_first.write(0, 2, u'优先级', style_heading)
        sheet_first.write(0, 3, u'负责人', style_heading)
        sheet_first.write(0, 4, u'创建时间', style_heading)
        sheet_first.write(0, 5, u'截止时间', style_heading)
        sheet_first.write(0, 6, u'完成时间', style_heading)
        sheet_first.write(0, 7, u'状态', style_heading)
        sheet_first.write(0, 8, u'类型', style_heading)
        sheet_first.write(0, 9, u'备注', style_heading)
        row = 1
        contents = TodoJob.objects.values('project_name', 'project_title', 'priority', 'manager', 'created_time', 'deadline_time',
            'completed_time', 'status', 'project_type', 'remark')
        for content in contents:
            sheet_first.write(row, 0, content['project_name'], style_body)
            sheet_first.write(row, 1, content['project_title'], style_body)
            if content['priority'] == 1:
                sheet_first.write(row, 2, u'Low', style_body)
            elif content['priority'] == 2:
                sheet_first.write(row, 2, u'Middle', style_body)
            elif content['priority'] == 3:
                sheet_first.write(row, 2, u'High', style_body)
            sheet_first.write(row, 3, content['manager'], style_body)
            sheet_first.write(row, 4, content['created_time'].strftime('%Y-%m-%d'), style_body)
            if content['deadline_time'].strftime('%Y-%m-%d') == '1970-01-01':
                sheet_first.write(row, 5, u'', style_body)
            else:
                sheet_first.write(row, 5, content['deadline_time'].strftime('%Y-%m-%d'), style_body)
            if content['completed_time'].strftime('%Y-%m-%d') == '1970-01-01':
                sheet_first.write(row, 6, u'', style_body)
            else:
                sheet_first.write(row, 6, content['completed_time'].strftime('%Y-%m-%d'), style_body)
            if content['status'] == 0:
                sheet_first.write(row, 7, u'已完成', style_body)
            else:
                sheet_first.write(row, 7, u'跟进中', style_red)
            if content['project_type'] == 0:
                sheet_first.write(row, 8, u'公共类', style_body)
            else:
                sheet_first.write(row, 8, u'项目单独', style_body)
            sheet_first.write(row, 9, content['remark'], style_body)

            # 第一行加宽
            sheet_first.col(0).width = 100 * 50
            sheet_first.col(1).width = 200 * 50
            sheet_first.col(2).width = 50 * 50
            sheet_first.col(3).width = 50 * 50
            sheet_first.col(4).width = 50 * 50
            sheet_first.col(5).width = 50 * 50
            sheet_first.col(6).width = 50 * 50
            sheet_first.col(7).width = 50 * 50
            sheet_first.col(8).width = 50 * 50
            sheet_first.col(9).width = 50 * 50
            row += 1
    elif modal == 'pain_point':
        sheet_name = u'痛点'
        sheet_first = wb.add_sheet(sheet_name)
        sheet_first.write(0, 0, u'项目', style_heading)
        sheet_first.write(0, 1, u'标题', style_heading)
        sheet_first.write(0, 2, u'提出人', style_heading)
        sheet_first.write(0, 3, u'当前处理人', style_heading)
        sheet_first.write(0, 4, u'创建时间', style_heading)
        sheet_first.write(0, 5, u'公共痛点', style_heading)
        row = 1
        contents = PainPoint.objects.values('project_name', 'project_title', 'manager', 'handler', 'created_time', 'project_type')
        for content in contents:
            sheet_first.write(row, 0, content['project_name'], style_body)
            sheet_first.write(row, 1, content['project_title'], style_body)
            sheet_first.write(row, 2, content['manager'], style_body)
            sheet_first.write(row, 3, content['handler'], style_body)
            sheet_first.write(row, 4, content['created_time'].strftime('%Y-%m-%d'), style_body)
            if content['project_type'] == 0:
                sheet_first.write(row, 5, u'否', style_body)
            else:
                sheet_first.write(row, 5, u'是', style_body)

            # 第一行加宽
            sheet_first.col(0).width = 100 * 50
            sheet_first.col(1).width = 200 * 50
            sheet_first.col(2).width = 50 * 50
            sheet_first.col(3).width = 50 * 50
            sheet_first.col(4).width = 50 * 50
            sheet_first.col(5).width = 50 * 50
            row += 1
    elif modal == 'kpi':
        sheet_name = u'关键KPI'
        sheet_first = wb.add_sheet(sheet_name)
        sheet_first.write(0, 0, u'标题', style_heading)
        sheet_first.write(0, 1, u'创建时间', style_heading)
        row = 1
        contents = KPI.objects.values('kpi_name', 'created_time')
        for content in contents:
            sheet_first.write(row, 0, content['kpi_name'], style_body)
            sheet_first.write(row, 1, content['created_time'], style_body)

            # 第一行加宽
            sheet_first.col(0).width = 200 * 50
            sheet_first.col(1).width = 50 * 50
            row += 1

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + modal + '.xls'
    response.write(output.getvalue())
    return response

#分发ajax请求
def dif_modal(request):
    modal_name = request.POST.get('modal_name')
    if modal_name == "chgPass":
        return change_password(request)
    elif modal_name == "delData":
        return del_data(request)
    elif modal_name == "addMonthJob":
        return add_month_job(request)
    elif modal_name == "editMonthJob":
        return edit_month_job(request)
    elif modal_name == "addKeyTaskJob":
        return add_key_task_job(request)
    elif modal_name == "editKeyTaskJob":
        return edit_key_task_job(request)
    elif modal_name == "addTodoJob":
        return add_todo_job(request)
    elif modal_name == "editTodoJob":
        return edit_todo_job(request)
    elif modal_name == "addPainPoint":
        return add_pain_point(request)
    elif modal_name == "editPainPoint":
        return edit_pain_point(request)
    elif modal_name == "addKPI":
        return add_kpi(request)
    elif modal_name == "editKPI":
        return edit_kpi(request)
    elif modal_name == "assignPainPoint":
        return assign_pain_point(request)
    elif modal_name == "applyPainPoint":
        return apply_pain_point(request)
    elif modal_name == "addComment":
        return add_comment(request)
    elif modal_name == "editComment":
        return edit_comment(request)
    elif modal_name == "delComment":
        return del_comment(request)
    elif modal_name == "addReply":
        return add_reply(request)
    elif modal_name == "editReply":
        return edit_reply(request)
    elif modal_name == "delReply":
        return del_reply(request)
    elif modal_name == "updateCommentRead":
        return update_comment_read(request)
    elif modal_name == "addDefaultProject":
        return add_default_project(request)
    elif modal_name == "editDefaultProject":
        return edit_default_project(request)
    elif modal_name == "delDefaultProject":
        return del_default_project(request)

def change_password(request):
    username = request.user.username
    old_password = request.POST.get('old_password')
    password1 = request.POST.get('password1')
    password2 = request.POST.get('password2')
    user = auth.authenticate(username=username, password=old_password)
    if user is not None and user.is_active:
        if password1 == "" or password2 == "":
            return HttpResponse(json.dumps({'status':'fail', 'id':'new_password_error', 'content':'●新密码不能为空'}))
        elif password1 == password2:
            u = User.objects.get(username__exact=username)
            u.set_password(password1)
            u.save()
            return HttpResponse(json.dumps({'status':'success', 'content':'/login'}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'new_password_error', 'content':'●密码不一致'}))
    else:
        return HttpResponse(json.dumps({'status':'fail', 'id':'old_password_error', 'content':'●旧密码错误'}))

#重置用户密码，这里隐藏页面，后门
def reset_password(request):
    u = User.objects.get(username__exact='sawyer')
    u.set_password('123456')
    u.save()
    return HttpResponse('猜猜这是什么')

#根据url删除对应表数据
def del_data(request):
    nid = request.POST.get('data_id')
    current_url = request.POST.get('current_url')
    label = current_url.split("/")[-2]
    if label == "month_job":
        time = request.GET.get('time')
        CurrentJob.objects.filter(id=nid).delete()
        logger.info(request.user.username + "-delete-CurrentJob(" + str(nid) + ")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/month_job/?time=' + time}))
    elif label == "todo_job":
        status = request.GET.get('status')
        TodoJob.objects.filter(id=nid).delete()
        logger.info(request.user.username + "-delete-TodoJob(" + str(nid) + ")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/todo_job/?status=' + status}))
    elif label == "pain_point":
        status = request.GET.get('status')
        PainPoint.objects.filter(id=nid).delete()
        logger.info(request.user.username + "-delete-PainPoint(" + str(nid) + ")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/pain_point/?status=' + status}))
    elif label == "kpi":
        time = request.GET.get('time')
        KPI.objects.filter(id=nid).delete()
        logger.info(request.user.username + "-delete-KPI(" + str(nid) + ")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/kpi/?time=' + time}))

def add_month_job(request):
    time = request.GET.get('time')
    now = datetime.now().strftime("%Y-%m-%d")
    username = request.user.username
    project_name = request.POST.get('project_name')
    job_content = request.POST.get('job_content')
    if not project_name:
        return HttpResponse(json.dumps({'status':'fail', 'id':'project_name_error', 'content':'●项目名称不能为空'}))
    else:
        CurrentJob.objects.create(project_name=project_name, manager=username, month_job_content=job_content, 
            created_time=now, edit_flag=0)
        logger.info(request.user.username + "-create-CurrentJob(" + str(project_name) + "," + str(username) + "," +\
            str(now) + "," + str(0) + ")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/month_job/?time=' + time}))

def edit_month_job(request):
    time = request.GET.get('time')
    nid = request.GET.get('id')
    project_name = request.POST.get('project_name')
    month_job_content = request.POST.get('month_job_content')
    first_week_job_content = request.POST.get('first_week_job_content')
    second_week_job_content = request.POST.get('second_week_job_content')
    third_week_job_content = request.POST.get('third_week_job_content')
    forth_week_job_content = request.POST.get('forth_week_job_content')
    fifth_week_job_content = request.POST.get('fifth_week_job_content')
    sixth_week_job_content = request.POST.get('sixth_week_job_content')
    flag = request.POST.get('edit_flag')
    if not project_name:
        return HttpResponse(json.dumps({'status':'fail', 'id':'project_name_error', 'content':'●项目名称不能为空'}))
    else:
        #每次更新数据之前取出edit_flag，更新之后edit_flag加1，为防止多人同时更新同一条操作
        edit_flag = CurrentJob.objects.filter(id=nid).values('edit_flag').first()['edit_flag']
        if int(flag) == int(edit_flag):
            CurrentJob.objects.filter(id=nid, edit_flag=flag).update(project_name=project_name, 
                month_job_content=month_job_content, first_week_job_content=first_week_job_content,
                second_week_job_content=second_week_job_content, third_week_job_content=third_week_job_content,
                forth_week_job_content=forth_week_job_content, fifth_week_job_content=fifth_week_job_content,
                sixth_week_job_content=sixth_week_job_content, edit_flag=int(flag)+1)
            logger.info(request.user.username + "-update-CurrentJob("+ str(nid) + "," + str(project_name) + "," +\
                str(int(flag)+1) + ")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/month_job/?time=' + time}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'alert'}))

def add_key_task_job(request):
    time = request.GET.get('time')
    nid = request.GET.get('id')
    month_key_task_job = request.POST.get('month_key_task_job')
    first_week_key_task_job = request.POST.get('first_week_key_task_job')
    second_week_key_task_job = request.POST.get('second_week_key_task_job')
    third_week_key_task_job = request.POST.get('third_week_key_task_job')
    forth_week_key_task_job = request.POST.get('forth_week_key_task_job')
    fifth_week_key_task_job = request.POST.get('fifth_week_key_task_job')
    sixth_week_key_task_job = request.POST.get('sixth_week_key_task_job')
    
    if month_key_task_job == "" and first_week_key_task_job == "" and second_week_key_task_job == "" and \
        third_week_key_task_job == "" and forth_week_key_task_job == "" and fifth_week_key_task_job == "" and \
        sixth_week_key_task_job == "":
        return HttpResponse(json.dumps({'status':'fail'}))
    else:
        pre_key_task_content = CurrentJob.objects.filter(id=nid).values('key_task').first()['key_task']
        pre_key_task_html_content = CurrentJob.objects.filter(id=nid).values('key_task_html').first()['key_task_html']
        month_key_task_job_content = ""
        first_week_key_task_job_content = ""
        second_week_key_task_job_content = ""
        third_week_key_task_job_content = ""
        forth_week_key_task_job_content = ""
        fifth_week_key_task_job_content = ""
        sixth_week_key_task_job_content = ""
        if month_key_task_job != "":
            month_key_task_job_content = month_key_task_job + "."
        if first_week_key_task_job != "":
            first_week_key_task_job_content = first_week_key_task_job + "."
        if second_week_key_task_job != "":
            second_week_key_task_job_content = second_week_key_task_job + "."
        if third_week_key_task_job != "":
            third_week_key_task_job_content = third_week_key_task_job + "."
        if forth_week_key_task_job != "":
            forth_week_key_task_job_content = forth_week_key_task_job + "."
        if fifth_week_key_task_job != "":
            fifth_week_key_task_job_content = fifth_week_key_task_job + "."
        if sixth_week_key_task_job != "":
            sixth_week_key_task_job_content = sixth_week_key_task_job + "."
        key_task_content = pre_key_task_content + month_key_task_job_content + first_week_key_task_job_content +\
            second_week_key_task_job_content + third_week_key_task_job_content + forth_week_key_task_job_content +\
            fifth_week_key_task_job_content + sixth_week_key_task_job_content
        key_task_html_content = pre_key_task_html_content + month_key_task_job_content + first_week_key_task_job_content +\
            second_week_key_task_job_content + third_week_key_task_job_content + forth_week_key_task_job_content +\
            fifth_week_key_task_job_content + sixth_week_key_task_job_content
        CurrentJob.objects.filter(id=nid).update(key_task=key_task_content, key_task_html=key_task_html_content)
        logger.info(request.user.username + "-update-CurrentJob-add_keytask(" + str(nid) + ")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/month_job/?time=' + time}))

def edit_key_task_job(request):
    time = request.GET.get('time')
    nid = request.GET.get('id')
    key_task_content = request.POST.get('key_task_content')
    key_task_html_content = request.POST.get('key_task_html_content')
    CurrentJob.objects.filter(id=nid).update(key_task=key_task_content, key_task_html=key_task_html_content)
    logger.info(request.user.username + "-update-CurrentJob-edit_keytask(" + str(nid) + ")")
    return HttpResponse(json.dumps({'status':'success', 'content':'/month_job/?time=' + time}))

def add_todo_job(request):
    now = datetime.now().strftime("%Y-%m-%d")
    username = request.user.username
    project_name = request.POST.get('project_name')
    project_title = request.POST.get('project_title')
    project_content = request.POST.get('project_content')
    priority = request.POST.get('priority')
    deadline_time = request.POST.get('deadline_time')
    status = request.POST.get('status')
    project_type = request.POST.get('project_type')
    remark = request.POST.get('remark')
    completed_time = "1970-01-01"
    if priority == "Low":
        priority = 1
    elif priority == "Middle":
        priority = 2
    elif priority == "High":
        priority = 3
    if not deadline_time:
        deadline_time = "1970-01-01"
    if status == u"跟进中":
        status = 1
    elif status ==u"已完成":
        status = 0
        completed_time = now
    if project_type == u"公共类":
        project_type = 0
    elif project_type == u"项目单独":
        project_type = 1
    if not project_name:
        return HttpResponse(json.dumps({'status':'fail', 'id':'project_name_error', 'content':'●项目名称不能为空'}))
    elif not project_title:
        return HttpResponse(json.dumps({'status':'fail', 'id':'project_title_error', 'content':'●标题不能为空'}))
    else:
        TodoJob.objects.create(project_name=project_name, project_title=project_title, project_content=project_content, 
            priority=priority, manager=username, created_time=now, deadline_time=deadline_time, completed_time=completed_time, 
            status=status, remark=remark, project_type=project_type, edit_flag=0)
        logger.info(request.user.username + "-create-TodoJob(" + str(project_name) + "," + str(project_title) + "," +\
            str(priority) + "," + str(username) + "," + str(now) + "," + str(deadline_time) + "," +\
            str(completed_time) + "," + str(status) + "," + str(remark) + "," + str(project_type) + "," + str(0) + ")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/todo_job/?status='}))

def edit_todo_job(request):
    now = datetime.now().strftime("%Y-%m-%d")
    nid = request.GET.get('id')
    project_name = request.POST.get('project_name')
    project_title = request.POST.get('project_title')
    project_content = request.POST.get('project_content')
    priority = request.POST.get('priority')
    deadline_time = request.POST.get('deadline_time')
    completed_time = "1970-01-01"
    status = request.POST.get('status')
    project_type = request.POST.get('project_type')
    remark = request.POST.get('remark')
    flag = request.POST.get('edit_flag')
    if priority == "Low":
        priority = 1
    elif priority == "Middle":
        priority = 2
    elif priority == "High":
        priority = 3
    if not deadline_time:
        deadline_time = "1970-01-01"
    if status == u"跟进中":
        status = 1
    elif status ==u"已完成":
        status = 0
        completed_time = now
    if project_type == u"公共类":
        project_type = 0
    elif project_type == u"项目单独":
        project_type = 1
    if not project_name:
        return HttpResponse(json.dumps({'status':'fail', 'id':'project_name_error', 'content':'●项目名称不能为空'}))
    elif not project_title:
        return HttpResponse(json.dumps({'status':'fail', 'id':'project_title_error', 'content':'●标题不能为空'}))
    else:
        #每次更新数据之前取出edit_flag，更新之后edit_flag加1，为防止多人同时更新同一条操作
        edit_flag = TodoJob.objects.filter(id=nid).values('edit_flag').first()['edit_flag']
        if int(flag) == int(edit_flag):
            TodoJob.objects.filter(id=nid).update(project_name=project_name, project_title=project_title, 
                project_content=project_content, priority=priority, deadline_time=deadline_time, completed_time=completed_time, 
                status=status, project_type=project_type, remark=remark, edit_flag=int(flag)+1)
            logger.info(request.user.username + "-update-TodoJob("+ str(nid) + "," + str(project_name) + "," + str(project_title) + "," +\
                str(priority) + "," + str(deadline_time) + "," + str(completed_time) + "," +\
                str(status) + "," + str(project_type) + "," + str(remark) + "," + str(int(flag)+1) + ")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/todo_job/?status='}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'alert'}))

def add_pain_point(request):
    now = datetime.now().strftime("%Y-%m-%d")
    username = request.user.username
    project_name = request.POST.get('project_name')
    project_title = request.POST.get('project_title')
    project_content = request.POST.get('project_content')
    plan = request.POST.get('plan')
    project_type = request.POST.get('project_type')
    status = request.POST.get('status')
    if project_type == u'是':
        project_type = 1
    elif project_type == u'否':
        project_type = 0
    if status == u'解决中':
        status = 1
    elif status == u'已解决':
        status = 0
    if not project_name:
        return HttpResponse(json.dumps({'status':'fail', 'id':'project_name_error', 'content':'●项目名称不能为空'}))
    elif not project_title:
        return HttpResponse(json.dumps({'status':'fail', 'id':'project_title_error', 'content':'●标题不能为空'}))
    else:
        PainPoint.objects.create(project_name=project_name, project_title=project_title, project_content=project_content,
            manager=username, handler="", created_time=now, project_type=project_type, plan=plan, status=status, edit_flag=0)
        logger.info(request.user.username + "-create-PainPoint(" + str(project_name) + "," + str(project_title) + "," +\
            str(username) + "," + str("") + "," + str(now) + "," + str(project_type) + "," +\
            str(plan) + "," + str(status) + "," + str(0) + ")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/pain_point/?status='}))

def edit_pain_point(request):
    nid = request.GET.get('id')
    project_name = request.POST.get('project_name')
    project_title = request.POST.get('project_title')
    project_content = request.POST.get('project_content')
    plan = request.POST.get('plan')
    project_type = request.POST.get('project_type')
    status = request.POST.get('status')
    flag = request.POST.get('edit_flag')
    if project_type == u"否":
        project_type = 0
    elif project_type == u"是":
        project_type = 1
    if status == u'解决中':
        status = 1
    elif status == u'已解决':
        status = 0
    if not project_name:
        return HttpResponse(json.dumps({'status':'fail', 'id':'project_name_error', 'content':'●项目名称不能为空'}))
    elif not project_title:
        return HttpResponse(json.dumps({'status':'fail', 'id':'project_title_error', 'content':'●标题不能为空'}))
    else:
        #每次更新数据之前取出edit_flag，更新之后edit_flag加1，为防止多人同时更新同一条操作
        edit_flag = PainPoint.objects.filter(id=nid).values('edit_flag').first()['edit_flag']
        if int(flag) == int(edit_flag):
            PainPoint.objects.filter(id=nid).update(project_name=project_name, project_title=project_title, 
                project_content=project_content, plan=plan, project_type=project_type, status=status, edit_flag=int(flag)+1)
            logger.info(request.user.username + "-update-PainPoint("+ str(nid) + "," + str(project_name) + "," +\
                str(project_title) + "," + str(project_type) + "," + str(status) + "," + str(int(flag)+1) + ")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/pain_point/?status='}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'alert'}))

#指派责任人，发送邮件，向新增责任人和剔除责任人分别发送邮件
def assign_pain_point(request):
    nid = request.POST.get('data_id')
    handler_list = request.POST.get('handler_list')
    handler_list = handler_list.replace('[','').replace(']','').replace('"','')
    if handler_list == '':
        handler_list = []
    else:
        handler_list = handler_list.split(',')
    handler = ",".join(handler_list)
    handlers = PainPoint.objects.filter(id=nid).values('handler').first()['handler']
    if handlers == '':
        handler_sql = []
    else:
        handler_sql = handlers.split(',')
    PainPoint.objects.filter(id=nid).update(handler=handler)
    logger.info(request.user.username + "-update-PainPoint-assign("+ str(nid) + "," + str(handler) + ")")

    #send_mail
    data = PainPoint.objects.filter(id=nid).values('project_name', 'project_title', 'manager').first()
    project_name = data['project_name']
    project_title = data['project_title']
    manager = data['manager']
    content = '项目名称：' + str(project_name) + ' ' + '标题：' + str(project_title) + ' ' + '提出人：' + str(manager)
    #新增责任人列表
    new_handlers_list = [h for h in handler_list if h not in handler_sql]
    #剔除责任人列表
    old_handlers_list = [h for h in handler_sql if h not in handler_list]
    if len(new_handlers_list):
        to_mail = []
        for u in new_handlers_list:
            if u == 'sawyer':
                to_mail.append('sawyersun@21kunpeng.com')
            else:
                to_mail.append(u + '@21kunpeng.com')
        send_mail.delay(to_mail, 'assign_new', content)
    if len(old_handlers_list):
        to_mail = []
        for u in old_handlers_list:
            if u == 'sawyer':
                to_mail.append('sawyersun@21kunpeng.com')
            else:
                to_mail.append(u + '@21kunpeng.com')
        send_mail.delay(to_mail, 'assign_old', content)
    return HttpResponse(json.dumps({'status':'success', 'content':'/pain_point/?status='}))

#申请痛点任务，发送邮件
def apply_pain_point(request):
    nid = request.POST.get('data_id')
    user = request.user.username
    handlers = PainPoint.objects.filter(id=nid).values('handler').first()['handler']
    if not handlers:
        handler = user
    else:
        handler = handlers + ',' + user
    PainPoint.objects.filter(id=nid).update(handler=handler)
    logger.info(request.user.username + "-update-PainPoint-apply("+ str(nid) + "," + str(handler) + ")")

    #send_mail
    data = PainPoint.objects.filter(id=nid).values('project_name', 'project_title', 'manager').first()
    project_name = data['project_name']
    project_title = data['project_title']
    manager = data['manager']
    content = '项目名称：' + str(project_name) + ' ' + '标题：' + str(project_title) + ' ' + '申请人：' + str(user)
    to_mail = []
    if manager == 'sawyer':
        to_mail.append('sawyersun@21kunpeng.com')
    else:
        to_mail.append(manager + '@21kunpeng.com')
    send_mail.delay(to_mail, 'apply', content)
    return HttpResponse(json.dumps({'status':'success', 'content':'/pain_point/?status='}))

def add_kpi(request):
    now = datetime.now().strftime("%Y-%m-%d")
    kpi_name = request.POST.get('kpi_name')
    kpi_content = request.POST.get('kpi_content')
    if not kpi_name:
        return HttpResponse(json.dumps({'status':'fail', 'id':'kpi_name_error', 'content':'●标题不能为空'}))
    else:
        KPI.objects.create(kpi_name=kpi_name, kpi_content=kpi_content, created_time=now, edit_flag=0)
        logger.info(request.user.username + "-create-KPI("+ str(kpi_name) + "," + str(now) + "," + str(0) + ")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/kpi/?time='}))

def edit_kpi(request):
    nid = request.GET.get('id')
    kpi_name = request.POST.get('kpi_name')
    kpi_content = request.POST.get('kpi_content')
    flag = request.POST.get('edit_flag')
    if not kpi_name:
        return HttpResponse(json.dumps({'status':'fail', 'id':'kpi_name_error', 'content':'●标题不能为空'}))
    else:
        #每次更新数据之前取出edit_flag，更新之后edit_flag加1，为防止多人同时更新同一条操作
        edit_flag = KPI.objects.filter(id=nid).values('edit_flag').first()['edit_flag']
        if int(flag) == int(edit_flag):
            KPI.objects.filter(id=nid).update(kpi_name=kpi_name, kpi_content=kpi_content, edit_flag=int(flag)+1)
            logger.info(request.user.username + "-update-KPI("+ str(nid) + "," + str(kpi_name) + "," + str(int(flag)+1) + ")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/kpi/?time='}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'alert'}))

def add_comment(request):
    owner_username = request.user.username
    target_username = request.POST.get('target_username')
    content = request.POST.get('content')
    created_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    parent_id_id = request.POST.get('parent_id_id')
    current_url = request.POST.get('current_url')
    label = current_url.split("/")[-2]
    label_url = current_url.split("/")[-1]
    if label == "edit_month_job":
        if content:
            CurrentJobComment.objects.create(owner_username=owner_username, target_username=target_username, content=content, 
                created_time=created_time, like_count=0, comment_id=0, parent_id_id=parent_id_id)
            logger.info(request.user.username + "-create-CurrentJobComment("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(0) + "," + str(parent_id_id) +")")
            CommentList.objects.create(owner_username=owner_username, target_username=target_username, created_time=created_time, 
                read=0, comment_url=current_url)
            logger.info(request.user.username + "-create-CommentList("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(current_url) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_month_job/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'add_comment_error', 'content':'●请输入评论内容！'}))
    elif label == "edit_todo_job":
        if content:
            TodoJobComment.objects.create(owner_username=owner_username, target_username=target_username, content=content, 
                created_time=created_time, like_count=0, comment_id=0, parent_id_id=parent_id_id)
            logger.info(request.user.username + "-create-TodoJobComment("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(0) + "," + str(parent_id_id) +")")
            CommentList.objects.create(owner_username=owner_username, target_username=target_username, created_time=created_time, 
                read=0, comment_url=current_url)
            logger.info(request.user.username + "-create-CommentList("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(current_url) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_todo_job/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'add_comment_error', 'content':'●请输入评论内容！'}))
    elif label == "edit_pain_point":
        if content:
            PainPointComment.objects.create(owner_username=owner_username, target_username=target_username, content=content, 
                created_time=created_time, like_count=0, comment_id=0, parent_id_id=parent_id_id)
            logger.info(request.user.username + "-create-PainPointComment("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(0) + "," + str(parent_id_id) +")")
            CommentList.objects.create(owner_username=owner_username, target_username=target_username, created_time=created_time, 
                read=0, comment_url=current_url)
            logger.info(request.user.username + "-create-CommentList("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(current_url) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_pain_point/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'add_comment_error', 'content':'●请输入评论内容！'}))

def edit_comment(request):
    nid = request.POST.get('id')
    content = request.POST.get('content')
    created_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    current_url = request.POST.get('current_url')
    label = current_url.split("/")[-2]
    label_url = current_url.split("/")[-1]
    if label == "edit_month_job":
        if content:
            CurrentJobComment.objects.filter(id=nid).update(content=content, created_time=created_time)
            logger.info(request.user.username + "-update-CurrentJobComment("+ str(nid) + "," + str(created_time) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_month_job/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'edit_comment_error', 'content':'●请输入评论内容！'}))
    elif label == "edit_todo_job":
        if content:
            TodoJobComment.objects.filter(id=nid).update(content=content, created_time=created_time)
            logger.info(request.user.username + "-update-TodoJobComment("+ str(nid) + "," + str(created_time) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_todo_job/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'edit_comment_error', 'content':'●请输入评论内容！'}))
    elif label == "edit_pain_point":
        if content:
            PainPointComment.objects.filter(id=nid).update(content=content, created_time=created_time)
            logger.info(request.user.username + "-update-PainPointComment("+ str(nid) + "," + str(created_time) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_pain_point/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'edit_comment_error', 'content':'●请输入评论内容！'}))

def del_comment(request):
    nid = request.POST.get('data_id')
    current_url = request.POST.get('current_url')
    label = current_url.split("/")[-2]
    label_url = current_url.split("/")[-1]
    if label == "edit_month_job":
        CurrentJobComment.objects.filter(id=nid).delete()
        CurrentJobComment.objects.filter(comment_id=nid).delete()
        logger.info(request.user.username + "-delete-CurrentJobComment("+ str(nid) +")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/edit_month_job/' + label_url}))
    elif label == "edit_todo_job":
        TodoJobComment.objects.filter(id=nid).delete()
        TodoJobComment.objects.filter(comment_id=nid).delete()
        logger.info(request.user.username + "-delete-TodoJobComment("+ str(nid) +")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/edit_todo_job/' + label_url}))
    elif label == "edit_pain_point":
        PainPointComment.objects.filter(id=nid).delete()
        PainPointComment.objects.filter(comment_id=nid).delete()
        logger.info(request.user.username + "-delete-PainPointComment("+ str(nid) +")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/edit_pain_point/' + label_url}))

def add_reply(request):
    owner_username = request.user.username
    comment_id = request.POST.get('comment_id')
    target_username = request.POST.get('target_username')
    content = request.POST.get('content')
    created_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    parent_id_id = request.POST.get('parent_id_id')
    current_url = request.POST.get('current_url')
    label = current_url.split("/")[-2]
    label_url = current_url.split("/")[-1]
    if label == "edit_month_job":
        if content:
            CurrentJobComment.objects.create(owner_username=owner_username, target_username=target_username, content=content, 
                created_time=created_time, like_count=0, comment_id=comment_id, parent_id_id=parent_id_id)
            logger.info(request.user.username + "-create-CurrentJobComment-reply("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(comment_id) + "," + str(parent_id_id) +")")
            CommentList.objects.create(owner_username=owner_username, target_username=target_username, created_time=created_time, 
                read=0, comment_url=current_url)
            logger.info(request.user.username + "-create-CommentList("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(current_url) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_month_job/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'add_comment_error', 'content':'●请输入评论内容！'}))
    elif label == "edit_todo_job":
        if content:
            TodoJobComment.objects.create(owner_username=owner_username, target_username=target_username, content=content, 
                created_time=created_time, like_count=0, comment_id=comment_id, parent_id_id=parent_id_id)
            logger.info(request.user.username + "-create-TodoJobComment-reply("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(comment_id) + "," + str(parent_id_id) +")")
            CommentList.objects.create(owner_username=owner_username, target_username=target_username, created_time=created_time, 
                read=0, comment_url=current_url)
            logger.info(request.user.username + "-create-CommentList("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(current_url) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_todo_job/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'add_comment_error', 'content':'●请输入评论内容！'}))
    elif label == "edit_pain_point":
        if content:
            PainPointComment.objects.create(owner_username=owner_username, target_username=target_username, content=content, 
                created_time=created_time, like_count=0, comment_id=comment_id, parent_id_id=parent_id_id)
            logger.info(request.user.username + "-create-PainPointComment-reply("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(comment_id) + "," + str(parent_id_id) +")")
            CommentList.objects.create(owner_username=owner_username, target_username=target_username, created_time=created_time, 
                read=0, comment_url=current_url)
            logger.info(request.user.username + "-create-CommentList("+ str(owner_username) + "," + str(target_username) + "," +\
                str(created_time) + "," + str(0) + "," + str(current_url) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_pain_point/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'add_comment_error', 'content':'●请输入评论内容！'}))

def edit_reply(request):
    nid = request.POST.get('id')
    content = request.POST.get('content')
    created_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    current_url = request.POST.get('current_url')
    label = current_url.split("/")[-2]
    label_url = current_url.split("/")[-1]
    if label == "edit_month_job":
        if content:
            CurrentJobComment.objects.filter(id=nid).update(content=content, created_time=created_time)
            logger.info(request.user.username + "-update-CurrentJobComment-reply("+ str(nid) + "," + str(created_time) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_month_job/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'edit_comment_error', 'content':'●请输入评论内容！'}))
    elif label == "edit_todo_job":
        if content:
            TodoJobComment.objects.filter(id=nid).update(content=content, created_time=created_time)
            logger.info(request.user.username + "-update-TodoJobComment-reply("+ str(nid) + "," + str(created_time) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_todo_job/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'edit_comment_error', 'content':'●请输入评论内容！'}))
    elif label == "edit_pain_point":
        if content:
            PainPointComment.objects.filter(id=nid).update(content=content, created_time=created_time)
            logger.info(request.user.username + "-update-PainPointComment-reply("+ str(nid) + "," + str(created_time) +")")
            return HttpResponse(json.dumps({'status':'success', 'content':'/edit_pain_point/' + label_url}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'edit_comment_error', 'content':'●请输入评论内容！'}))

def del_reply(request):
    nid = request.POST.get('data_id')
    current_url = request.POST.get('current_url')
    label = current_url.split("/")[-2]
    label_url = current_url.split("/")[-1]
    if label == "edit_month_job":
        CurrentJobComment.objects.filter(id=nid).delete()
        logger.info(request.user.username + "-delete-CurrentJobComment-reply("+ str(nid) +")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/edit_month_job/' + label_url}))
    elif label == "edit_todo_job":
        TodoJobComment.objects.filter(id=nid).delete()
        logger.info(request.user.username + "-delete-TodoJobComment-reply("+ str(nid) +")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/edit_todo_job/' + label_url}))
    elif label == "edit_pain_point":
        PainPointComment.objects.filter(id=nid).delete()
        logger.info(request.user.username + "-delete-PainPointComment-reply("+ str(nid) +")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/edit_pain_point/' + label_url}))

def query_comment_list(username):
    comment_list = []
    comments = CommentList.objects.filter(target_username=username, read=0).values('id', 'owner_username', 'target_username',
        'created_time', 'comment_url')
    for d in comments:
        table = {}
        table = {
            'id': d['id'],
            'owner_username': d['owner_username'],
            'target_username': d['target_username'],
            'created_time': d['created_time'],
            'comment_url': d['comment_url']
        }
        comment_list.append(table)
    return comment_list

def update_comment_read(request):
    nid = request.POST.get('comment_id')
    CommentList.objects.filter(id=nid).update(read=1)
    logger.info(request.user.username + "-update-CommentList("+ str(1) +")")

def add_default_project(request):
    default_project_name = request.POST.get('add_default_project_name')
    if default_project_name:
        CurrentJobList.objects.create(project_name=default_project_name, manager=request.user.username)
        logger.info(request.user.username + "-create-CurrentJobList("+ str(default_project_name) + "," + str(request.user.username)+")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/default_project/'}))
    else:
        return HttpResponse(json.dumps({'status':'fail', 'id':'add_default_project_name_error', 'content':'●请输入项目名称！'}))

def edit_default_project(request):
    data_id = request.POST.get('data_id')
    default_project_name = request.POST.get('edit_default_project_name')
    if default_project_name:
        CurrentJobList.objects.filter(id=data_id).update(project_name=default_project_name)
        logger.info(request.user.username + "-update-CurrentJobList("+ str(data_id) + "," + str(default_project_name) +")")
        return HttpResponse(json.dumps({'status':'success', 'content':'/default_project/'}))
    else:
        return HttpResponse(json.dumps({'status':'fail', 'id':'edit_default_project_name_error', 'content':'●请输入项目名称！'}))

def del_default_project(request):
    data_id = request.POST.get('data_id')
    CurrentJobList.objects.filter(id=data_id).delete()
    logger.info(request.user.username + "-delete-CurrentJobList("+ str(data_id) +")")
    return HttpResponse(json.dumps({'status':'success', 'content':'/default_project/'}))