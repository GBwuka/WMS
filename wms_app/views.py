import calendar
import logging

from datetime import datetime
from datetime import timedelta
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.db.models import Avg, Max, Min, Count, Sum

from .models import CurrentJob, TodoJob, PainPoint, KPI, CurrentJobComment, TodoJobComment, PainPointComment, CommentList, CurrentJobList
from .func_utils import dif_modal, kindeditor_style, query_comment_list

logger = logging.getLogger('wms.wms_app.views')

def homepage(request):
    return render(request, 'login.html')

@csrf_exempt
def login(request):
    logger.info("-login")
    if request.method == 'POST':
        user_form = request.POST
        username = user_form.get('username')
        password = user_form.get('password')
        user = auth.authenticate(username=username, password=password)
        if not username:
            return render(request, 'login.html', {'username_error': '●用户名为空'})
        elif user is not None and user.is_active:
            auth.login(request, user)
            now = datetime.now().strftime("%Y-%m")
            return redirect('/wms/month_job/?time=' + now)
        else:
            return render(request, 'login.html', {'password_error': '●密码错误'})
    return render(request, 'login.html')

@login_required
def logout(request):
    logger.info(request.user.username + "-logout")
    auth.logout(request)
    return render(request, 'login.html')

@csrf_exempt
@login_required
def month_job(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        time = request.GET.get('time')
        years = []
        years_months = []
        years_months_dict = {}
        times = CurrentJob.objects.values_list('created_time')
        for t in times:
            years.append(t[0].strftime("%Y"))
            years_months.append(t[0].strftime("%Y-%m"))
        years_list = list(set(years))
        years_list.sort()
        for y in years_list:
            years_months_list = []
            for y_m in years_months:
                if y_m.startswith(y):
                    years_months_list.append(y_m.split('-')[1])
                    years_months_list_sorted = list(set(years_months_list))
                    years_months_list_sorted.sort()
            years_months_dict[y] = years_months_list_sorted
        years_months_dict_sorted = sorted(years_months_dict.items(), key=lambda d: d[0])
        if not time:
            table_data = CurrentJob.objects.values().order_by('created_time')
        else:
            year = time.split('-')[0]
            month = time.split('-')[1]
            table_data = CurrentJob.objects.filter(created_time__year=year, created_time__month=month)\
                .values().order_by('created_time')
        tables = []
        for d in table_data:
            if request.user.username == d['manager'] or request.user.is_superuser:
                able = True
            else:
                able = False
            if request.user.is_superuser:
                key_task_able = True
            else:
                key_task_able = False
            table = {}
            table = {
                'id': d['id'],
                'project_name': d['project_name'],
                'manager': d['manager'],
                'key_task': d['key_task'],
                'key_task_able': key_task_able,
                'created_time': d['created_time'].strftime("%Y-%m-%d"),
                'able': able
            }
            tables.append(table)
        return render(request, 'month_job.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'navbar_brand_data': years_months_dict_sorted, 'table_data': tables, 'time': time})

@csrf_exempt
@login_required
def add_month_job(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        time = request.GET.get('time')
        return render(request, 'add_month_job.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'kindeditor_style':kindeditor_style, 'time': time})

@csrf_exempt
@login_required
def edit_month_job(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        time = request.GET.get('time')
        nid = request.GET.get('id')
        editable = request.GET.get('editable')
        data = CurrentJob.objects.filter(id=nid).values().first()
        project_name = data['project_name']
        manager = data['manager']
        month_job_content = data['month_job_content']
        year = data['created_time'].strftime("%Y")
        month = data['created_time'].strftime("%m")
        first_week_job_content = data['first_week_job_content']
        second_week_job_content = data['second_week_job_content']
        third_week_job_content = data['third_week_job_content']
        forth_week_job_content = data['forth_week_job_content']
        fifth_week_job_content = data['fifth_week_job_content']
        sixth_week_job_content = data['sixth_week_job_content']
        edit_flag = data['edit_flag']
        month_job_content = month_job_content.replace("\n","").replace("\'","\"")
        first_week_job_content = first_week_job_content.replace("\n","").replace("\'","\"")
        second_week_job_content = second_week_job_content.replace("\n","").replace("\'","\"")
        third_week_job_content = third_week_job_content.replace("\n","").replace("\'","\"")
        forth_week_job_content = forth_week_job_content.replace("\n","").replace("\'","\"")
        fifth_week_job_content = fifth_week_job_content.replace("\n","").replace("\'","\"")
        sixth_week_job_content = sixth_week_job_content.replace("\n","").replace("\'","\"")
        if request.user.is_superuser:
            issuper = 1
        else:
            issuper = 0
        weeks = calendar.monthcalendar(int(year), int(month))
        week_list = [i+1 for i in range(len(weeks))]
        week_dict_value = ["first", "second", "third", "forth", "fifth", "sixth"]
        week_dict = dict(zip(week_list, week_dict_value))

        #获取该工作的所有评论
        mj = CurrentJob.objects.get(id=nid)
        mj_comments = mj.currentjobcomment_set.values('id', 'owner_username', 'target_username', 'content', 'created_time', 'comment_id')
        #评论列表
        mj_comments_list = []
        for mjc in mj_comments:
            #评论字典
            mj_comments_dict = {}
            mjc_content = mjc['content'].replace("\n","").replace("\'","\"")
            #这里True,False以字符串形式是为了防止前端报错
            if mjc['owner_username'] == request.user.username or request.user.is_superuser:
                comment_editable = 'True'
            else:
                comment_editable = 'False'
            #统计回复列表
            #回复列表
            mj_replys_list = []
            mj_replys_list_sorted = []
            if not mjc['comment_id']:
                #统计评论列表
                mj_comments_dict = {
                    'id': mjc['id'],
                    'owner_username': mjc['owner_username'],
                    'target_username': mjc['target_username'],
                    'content': mjc_content,
                    'created_time': mjc['created_time'],
                    'comment_id': mjc['comment_id'],
                    'comment_editable': comment_editable
                }

                mj_replys = mj.currentjobcomment_set.filter(comment_id=mjc['id']).values('id', 'owner_username', 
                    'target_username', 'content', 'created_time')
                for mjr in mj_replys:
                    #回复字典
                    mj_replys_dict = {}
                    mjr_content = mjr['content'].replace("\n","").replace("\'","\"")
                    if mjr['owner_username'] == request.user.username or request.user.is_superuser:
                        reply_editable = 'True'
                    else:
                        reply_editable = 'False'
                    mj_replys_dict = {
                        'id': mjr['id'],
                        'owner_username': mjr['owner_username'],
                        'target_username': mjr['target_username'],
                        'content': mjr_content,
                        'created_time': mjr['created_time'],
                        'reply_editable': reply_editable
                    }
                    mj_replys_list.append(mj_replys_dict)
                mj_replys_list_sorted = sorted(mj_replys_list, key=lambda d: d['created_time'], reverse=True)
                mj_comments_dict['reply_list'] = mj_replys_list_sorted
                mj_comments_list.append(mj_comments_dict)
        mj_comments_list_sorted = sorted(mj_comments_list, key=lambda d: d['created_time'], reverse=True)
        return render(request, 'edit_month_job.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username':request.user.username, 'project_name':project_name,
            'month_job_content':month_job_content, 'first_week_job_content':first_week_job_content, 
            'second_week_job_content':second_week_job_content, 'third_week_job_content':third_week_job_content, 
            'forth_week_job_content':forth_week_job_content, 'fifth_week_job_content':fifth_week_job_content,
            'sixth_week_job_content':sixth_week_job_content, 'weeks':week_dict, 'editable':editable, 
            'kindeditor_style':kindeditor_style, 'edit_flag':edit_flag, 'time':time, 'issuper':issuper,
            'target_username':manager, 'parent_id_id':nid, 'comment_list':mj_comments_list_sorted})

@csrf_exempt
@login_required
def edit_key_task_job(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        time = request.GET.get('time')
        nid = request.GET.get('id')
        editable = request.GET.get('editable')
        key_task_html_content = CurrentJob.objects.filter(id=nid).values('key_task_html').first()['key_task_html']
        if key_task_html_content:
            key_task_content = key_task_html_content
        else:
            key_task_content = CurrentJob.objects.filter(id=nid).values('key_task').first()['key_task']
        key_task_content = key_task_content.replace("\n","").replace("\'","\"")

        return render(request, 'edit_key_task_job.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'key_task_content': key_task_content,
            'editable':editable, 'kindeditor_style':kindeditor_style, 'time': time})

@csrf_exempt
@login_required
def todo_job(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        now = datetime.now().strftime("%Y-%m-%d")
        status = request.GET.get('status')
        if not status:
            table_data = TodoJob.objects.values()
        else:
            table_data = TodoJob.objects.filter(status=status).values()
        table_data_common = table_data.filter(project_type=0)
        tables_common = []
        for d in table_data_common:
            isred = 0
            if request.user.username == d['manager'] or request.user.is_superuser:
                able = True
            else:
                able = False
            if d['priority'] == 1:
                priority = 'Low'
            elif d['priority'] == 2:
                priority = 'Middle'
            elif d['priority'] == 3:
                priority = 'High'
            if d['completed_time'].strftime("%Y-%m-%d") == "1970-01-01":
                completed_time = ""
            else:
                completed_time = d['completed_time'].strftime("%Y-%m-%d")
            if d['deadline_time'].strftime("%Y-%m-%d") == "1970-01-01":
                deadline_time = ""
            else:
                deadline_time = d['deadline_time'].strftime("%Y-%m-%d")
                if deadline_time <= now:
                    isred = 1
            if d['status'] == 1:
                status = u'跟进中'
            elif d['status'] == 0:
                status = u'已完成'
                isred = 0
            table_common = {}
            table_common = {
                'id': d['id'],
                'project_name': d['project_name'],
                'project_title': d['project_title'],
                'priority': priority,
                'manager': d['manager'],
                'created_time': d['created_time'].strftime("%Y-%m-%d"),
                'deadline_time': deadline_time,
                'completed_time': completed_time,
                'status': status,
                'remark': d['remark'],
                'able': able,
                'isred': isred
            }
            tables_common.append(table_common)
        table_data_single = table_data.filter(project_type=1)
        tables_single = []
        for d in table_data_single:
            isred = 0
            if request.user.username == d['manager'] or request.user.is_superuser:
                able = True
            else:
                able = False
            if d['priority'] == 1:
                priority = 'Low'
            elif d['priority'] == 2:
                priority = 'Middle'
            elif d['priority'] == 3:
                priority = 'High'
            if d['completed_time'].strftime("%Y-%m-%d") == "1970-01-01":
                completed_time = ""
            else:
                completed_time = d['completed_time'].strftime("%Y-%m-%d")
            if d['deadline_time'].strftime("%Y-%m-%d") == "1970-01-01":
                deadline_time = ""
            else:
                deadline_time = d['deadline_time'].strftime("%Y-%m-%d")
                if deadline_time <= now:
                    isred = 1
            if d['status'] == 1:
                status = u'跟进中'
            elif d['status'] == 0:
                status = u'已完成'
                isred = 0
            table_single = {}
            table_single = {
                'id': d['id'],
                'project_name': d['project_name'],
                'project_title': d['project_title'],
                'priority': priority,
                'manager': d['manager'],
                'created_time': d['created_time'].strftime("%Y-%m-%d"),
                'deadline_time': deadline_time,
                'completed_time': completed_time,
                'status': status,
                'remark': d['remark'],
                'able': able,
                'isred': isred
            }
            tables_single.append(table_single)
        return render(request, 'todo_job.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'table_data_common': tables_common,
            'table_data_single': tables_single})

@csrf_exempt
@login_required
def add_todo_job(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        return render(request, 'add_todo_job.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'kindeditor_style':kindeditor_style})

@csrf_exempt
@login_required
def edit_todo_job(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        nid = request.GET.get('id')
        editable = request.GET.get('editable')
        data = TodoJob.objects.filter(id=nid).values().first()
        project_name = data['project_name']
        project_title = data['project_title']
        project_content = data['project_content']
        priority = data['priority']
        manager = data['manager']
        deadline_time = data['deadline_time']
        status = data['status']
        remark = data['remark']
        project_type = data['project_type']
        edit_flag = data['edit_flag']

        project_content = project_content.replace("\n","").replace("\'","\"")
        if priority == 1:
            priority = 'Low'
        elif priority == 2:
            priority = 'Middle'
        elif priority == 3:
            priority = 'High'
        if status == 1:
            status = u'跟进中'
        elif status == 0:
            status = u'已完成'
        if project_type == 1:
            project_type = u'项目单独'
        elif project_type == 0:
            project_type = u'公共类'
        if deadline_time.strftime("%Y-%m-%d") == '1970-01-01':
            deadline_time = ''
        else:
            deadline_time = deadline_time.strftime("%Y-%m-%d")

        #获取该工作的所有评论
        tdj = TodoJob.objects.get(id=nid)
        tdj_comments = tdj.todojobcomment_set.values('id', 'owner_username', 'target_username', 'content', 'created_time', 'comment_id')
        #评论列表
        tdj_comments_list = []
        for tdjc in tdj_comments:
            #评论字典
            tdj_comments_dict = {}
            tdjc_content = tdjc['content'].replace("\n","").replace("\'","\"")
            #这里True,False以字符串形式是为了防止前端报错
            if tdjc['owner_username'] == request.user.username or request.user.is_superuser:
                comment_editable = 'True'
            else:
                comment_editable = 'False'
            #统计回复列表
            #回复列表
            tdj_replys_list = []
            tdj_replys_list_sorted = []
            if not tdjc['comment_id']:
                #统计评论列表
                tdj_comments_dict = {
                    'id': tdjc['id'],
                    'owner_username': tdjc['owner_username'],
                    'target_username': tdjc['target_username'],
                    'content': tdjc_content,
                    'created_time': tdjc['created_time'],
                    'comment_id': tdjc['comment_id'],
                    'comment_editable': comment_editable
                }

                tdj_replys = tdj.todojobcomment_set.filter(comment_id=tdjc['id']).values('id', 'owner_username', 
                    'target_username', 'content', 'created_time')
                for tdjr in tdj_replys:
                    #回复字典
                    tdj_replys_dict = {}
                    tdjr_content = tdjr['content'].replace("\n","").replace("\'","\"")
                    if tdjr['owner_username'] == request.user.username or request.user.is_superuser:
                        reply_editable = 'True'
                    else:
                        reply_editable = 'False'
                    tdj_replys_dict = {
                        'id': tdjr['id'],
                        'owner_username': tdjr['owner_username'],
                        'target_username': tdjr['target_username'],
                        'content': tdjr_content,
                        'created_time': tdjr['created_time'],
                        'reply_editable': reply_editable
                    }
                    tdj_replys_list.append(tdj_replys_dict)
                tdj_replys_list_sorted = sorted(tdj_replys_list, key=lambda d: d['created_time'], reverse=True)
                tdj_comments_dict['reply_list'] = tdj_replys_list_sorted
                tdj_comments_list.append(tdj_comments_dict)
        tdj_comments_list_sorted = sorted(tdj_comments_list, key=lambda d: d['created_time'], reverse=True)
        return render(request, 'edit_todo_job.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'project_name': project_name,
            'project_title': project_title, 'project_content':project_content, 'priority':priority, 'deadline_time': deadline_time,
            'status':status, 'remark':remark, 'project_type':project_type, 'editable':editable, 'kindeditor_style':kindeditor_style, 
            'edit_flag':edit_flag, 'target_username':manager, 'parent_id_id':nid, 'comment_list':tdj_comments_list_sorted})

@csrf_exempt
@login_required
def pain_point(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        status = request.GET.get('status')
        if not status:
            table_data = PainPoint.objects.values()
        else:
            table_data = PainPoint.objects.filter(status=status).values()
        tables = []
        for d in table_data:
            handler_list = d['handler'].split(',')
            if request.user.is_superuser:
                able = True
            else:
                if not d['handler']:
                    if request.user.username == d['manager']:
                        able = True
                    else:
                        able = False
                else:
                    if request.user.username in handler_list:
                        able = True
                    else:
                        able = False
            if request.user.username in handler_list:
                apply_able = False
            else:
                apply_able = True
            if request.user.is_superuser:
                assign_able = True
            else:
                if request.user.username == d['manager']:
                    assign_able = True
                else:
                    assign_able = False
            if d['project_type'] == 1:
                project_type = u'是'
            elif d['project_type'] == 0:
                project_type = u'否'
            if d['status'] == 1:
                status = u'解决中'
            elif d['status'] == 0:
                status = u'已解决'
            table = {}
            table = {
                'id': d['id'],
                'project_name': d['project_name'],
                'project_title': d['project_title'],
                'project_content': d['project_content'],
                'manager': d['manager'],
                'handler': d['handler'],
                'created_time': d['created_time'].strftime("%Y-%m-%d"),
                'project_type': project_type,
                'status': status,
                'able': able,
                'apply_able': apply_able,
                'assign_able': assign_able
            }
            tables.append(table)
        return render(request, 'pain_point.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'table_data': tables})

@csrf_exempt
@login_required
def add_pain_point(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        return render(request, 'add_pain_point.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'kindeditor_style':kindeditor_style})

@csrf_exempt
@login_required
def edit_pain_point(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        nid = request.GET.get('id')
        editable = request.GET.get('editable')
        data = PainPoint.objects.filter(id=nid).values().first()
        project_name = data['project_name']
        project_title = data['project_title']
        project_content = data['project_content']
        manager = data['manager']
        plan = data['plan']
        project_type = data['project_type']
        status = data['status']
        edit_flag = data['edit_flag']

        project_content = project_content.replace("\n","").replace("\'","\"")
        plan = plan.replace("\n","").replace("\'","\"")
        if project_type == 1:
            project_type = u'是'
        elif project_type == 0:
            project_type = u'否'
        if status == 1:
            status = u'解决中'
        elif status == 0:
            status = u'已解决'

        #获取该工作的所有评论
        pp = PainPoint.objects.get(id=nid)
        pp_comments = pp.painpointcomment_set.values('id', 'owner_username', 'target_username', 'content', 'created_time', 'comment_id')
        #评论列表
        pp_comments_list = []
        for ppc in pp_comments:
            #评论字典
            pp_comments_dict = {}
            ppc_content = ppc['content'].replace("\n","").replace("\'","\"")
            #这里True,False以字符串形式是为了防止前端报错
            if ppc['owner_username'] == request.user.username or request.user.is_superuser:
                comment_editable = 'True'
            else:
                comment_editable = 'False'
            #统计回复列表
            #回复列表
            pp_replys_list = []
            pp_replys_list_sorted = []
            if not ppc['comment_id']:
                #统计评论列表
                pp_comments_dict = {
                    'id': ppc['id'],
                    'owner_username': ppc['owner_username'],
                    'target_username': ppc['target_username'],
                    'content': ppc_content,
                    'created_time': ppc['created_time'],
                    'comment_id': ppc['comment_id'],
                    'comment_editable': comment_editable
                }

                pp_replys = pp.painpointcomment_set.filter(comment_id=ppc['id']).values('id', 'owner_username', 
                    'target_username', 'content', 'created_time')
                for ppr in pp_replys:
                    #回复字典
                    pp_replys_dict = {}
                    ppr_content = ppr['content'].replace("\n","").replace("\'","\"")
                    if ppr['owner_username'] == request.user.username or request.user.is_superuser:
                        reply_editable = 'True'
                    else:
                        reply_editable = 'False'
                    pp_replys_dict = {
                        'id': ppr['id'],
                        'owner_username': ppr['owner_username'],
                        'target_username': ppr['target_username'],
                        'content': ppr_content,
                        'created_time': ppr['created_time'],
                        'reply_editable': reply_editable
                    }
                    pp_replys_list.append(pp_replys_dict)
                pp_replys_list_sorted = sorted(pp_replys_list, key=lambda d: d['created_time'], reverse=True)
                pp_comments_dict['reply_list'] = pp_replys_list_sorted
                pp_comments_list.append(pp_comments_dict)
        pp_comments_list_sorted = sorted(pp_comments_list, key=lambda d: d['created_time'], reverse=True)
        return render(request, 'edit_pain_point.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'project_name': project_name,
            'project_title': project_title, 'project_content':project_content, 'plan':plan, 'project_type':project_type,
            'status': status, 'editable':editable, 'kindeditor_style':kindeditor_style, 'edit_flag':edit_flag,
            'target_username':manager, 'parent_id_id':nid, 'comment_list':pp_comments_list_sorted})

@csrf_exempt
@login_required
def kpi(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        time = request.GET.get('time')
        years = []
        years_months = []
        years_months_dict = {}
        times = KPI.objects.values_list('created_time')
        for t in times:
            years.append(t[0].strftime("%Y"))
            years_months.append(t[0].strftime("%Y-%m"))
        years_list = list(set(years))
        years_list.sort()
        for y in years_list:
            years_months_list = []
            for y_m in years_months:
                if y_m.startswith(y):
                    if int(y_m.split('-')[1]) >=1 and int(y_m.split('-')[1]) <= 6:
                        if u"上半年" not in years_months_list:
                            years_months_list.append("上半年")
                    else:
                        if u"下半年" not in years_months_list:
                            years_months_list.append("下半年")
                    years_months_list_sorted = list(set(years_months_list))
                    years_months_list_sorted.sort()
            years_months_dict[y] = years_months_list_sorted
        years_months_dict_sorted = sorted(years_months_dict.items(), key=lambda d: d[0])
        if not time:
            table_data = KPI.objects.values().order_by('created_time')
        else:
            year = time.split('-')[0]
            half_year = time.split('-')[1]
            if half_year == u"上半年":
                table_data = KPI.objects.filter(created_time__year=year, created_time__month__lte=6)\
                    .values().order_by('created_time')
            elif half_year == u"下半年":
                table_data = KPI.objects.filter(created_time__year=year, created_time__month__gte=7)\
                    .values().order_by('created_time')
        tables = []
        for d in table_data:
            if request.user.is_superuser:
                able = True
            else:
                able = False
            table = {}
            table = {
                'id': d['id'],
                'kpi_name': d['kpi_name'],
                'kpi_content': d['kpi_content'],
                'created_time': d['created_time'].strftime("%Y-%m-%d"),
                'able': able
            }
            tables.append(table)
        if request.user.is_superuser:
            btn_able = "true"
        else:
            btn_able = "false"
        return render(request, 'kpi.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'navbar_brand_data': years_months_dict_sorted,
            'table_data': tables, 'btn_able': btn_able})

@csrf_exempt
@login_required
def add_kpi(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        return render(request, 'add_kpi.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'kindeditor_style':kindeditor_style})

@csrf_exempt
@login_required
def edit_kpi(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        nid = request.GET.get('id')
        editable = request.GET.get('editable')
        data = KPI.objects.filter(id=nid).values().first()
        kpi_name = data['kpi_name']
        kpi_content = data['kpi_content']
        edit_flag = data['edit_flag']

        kpi_content = kpi_content.replace("\n","").replace("\'","\"")
        return render(request, 'edit_kpi.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'kpi_name': kpi_name,
            'kpi_content': kpi_content, 'editable':editable, 'kindeditor_style':kindeditor_style, 'edit_flag':edit_flag})

@csrf_exempt
@login_required
def key_task_timeline(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        time = request.GET.get('time')
        years = []
        years_months = []
        years_months_dict = {}
        times = CurrentJob.objects.values_list('created_time')
        for t in times:
            years.append(t[0].strftime("%Y"))
            years_months.append(t[0].strftime("%Y-%m"))
        years_list = list(set(years))
        years_list.sort()
        for y in years_list:
            years_months_list = []
            for y_m in years_months:
                if y_m.startswith(y):
                    years_months_list.append(y_m.split('-')[1])
                    years_months_list_sorted = list(set(years_months_list))
                    years_months_list_sorted.sort()
            years_months_dict[y] = years_months_list_sorted
        years_months_dict_sorted = sorted(years_months_dict.items(), key=lambda d: d[0])

        timeline_list = []
        timeline_data = {}
        if not time:
            data = CurrentJob.objects.values('created_time')
            date_list = []
            for d in data:
                date_list.append(d['created_time'].strftime("%Y-%m"))
            date_set = sorted(set(date_list))
            index = 0
            for ds in date_set:
                index += 1
                timeline = []
                year = ds.split('-')[0]
                month = ds.split('-')[1]
                data = CurrentJob.objects.filter(created_time__year=year, created_time__month=month)\
                    .values().order_by('created_time')
                for d in data:
                    table = {}
                    if d['key_task']:
                        table = {
                            'id': d['id'],
                            'project_name': d['project_name'],
                            'key_task': d['key_task']
                        }
                    timeline.append(table)
                timeline_data = {
                    'time': ds,
                    'count': index % 2,
                    'content': timeline
                }
                timeline_list.append(timeline_data)
        else:
            timeline = []
            year = time.split('-')[0]
            month = time.split('-')[1]
            data = CurrentJob.objects.filter(created_time__year=year, created_time__month=month)\
                .values().order_by('created_time')
            for d in data:
                table = {}
                if d['key_task']:
                    table = {
                        'id': d['id'],
                        'project_name': d['project_name'],
                        'key_task': d['key_task']
                    }
                timeline.append(table)
            timeline_data = {
                'time': time,
                'count': 1,
                'content': timeline
            }
            timeline_list.append(timeline_data)
        return render(request, 'key_task_timeline.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 
            'navbar_brand_data': years_months_dict_sorted, 'timeline_list': timeline_list})

@csrf_exempt
@login_required
def comment_list(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        table_data = CommentList.objects.filter(target_username=request.user.username).values('id', 'owner_username', 'created_time', 
            'read', 'comment_url')
        tables = []
        for d in table_data:
            if d['read']:
                is_read = '已读'
            else:
                is_read = '未读'
            table = {}
            table = {
                'id': d['id'],
                'owner_username': d['owner_username'],
                'created_time': d['created_time'],
                'read': is_read,
                'comment_url': d['comment_url']
            }
            tables.append(table)
        return render(request, 'comment_list.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'table_data': tables})

@csrf_exempt
@login_required
def default_project(request):
    logger.info(request.user.username + "-" + request.get_full_path())
    if request.is_ajax():
        return dif_modal(request)
    else:
        comment_list_read = query_comment_list(request.user.username)
        table_data = CurrentJobList.objects.filter(manager=request.user.username).values('id', 'project_name')
        tables = []
        for d in table_data:
            table = {}
            table = {
                'id': d['id'],
                'project_name': d['project_name'],
            }
            tables.append(table)
        return render(request, 'default_project.html', {'comment_list_read': comment_list_read, 'comment_len': len(comment_list_read),
            'username': request.user.username, 'table_data': tables})