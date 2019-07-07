import re
from .models import User
from django import http
from django.shortcuts import render
from django.views import View
from django.contrib.auth import login,authenticate
from meiduo_mall.utils.response_code import RETCODE
from django_redis import get_redis_connection
# Create your views here.

class RegisterView(View):

    def get(self,request):
        return render(request,'register.html')


    def post(self,request):
        """注册"""
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        password2 = query_dict.get('password2')
        mobile = query_dict.get('mobile')
        sms_code_client = query_dict.get('sms_code')
        allow = query_dict.get('allow')
        """校验"""
        if not all([username,password,password2,mobile,sms_code_client,allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        if password != password2:
            return http.HttpResponseForbidden('两次密码输入的不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')

        #创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        #获取短信验证码
        sms_code_server =redis_conn.get('sms_code_%s'%mobile)
        #让短信验证码只能用一次
        redis_conn.delete('sms_code_%s'%mobile)
        #判断是否过期
        if sms_code_server is None:
            return http.HttpResponseForbidden('短信验证码过期')
        #判断输入是否正确
        if sms_code_client != sms_code_server.decode():
            return http.HttpResponseForbidden('短信验证码输入错误')







        #创建新用户
        user = User.objects.create_user(username=username,password=password,mobile=mobile)
        login(request,user)
        return http.HttpResponse('注册成功，跳转到首页')


class UsernameCountView(View):
    """判断用户是否重复注册"""
    def get(self,request,username):
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK,'errmsg':'OK','count':count})

class MobileCountView(View):
        #"""判断手机号是否重复注册"""

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class LoginView(View):
    def get(self,request):
        return render(request,'login.html')

    def post(self,request):
        #接收前端传入的表单数据
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')

        #判断用户是否是用手机登录，若是的 认证时 就用手机号查询
        if re.match(r'^1[3-9]\d{9}$',username):
            User.USERNAME_FIELD = 'mobile'
        #校验
        user = authenticate(request,username=username,password=password)
        User.USERNAME_FIELD = 'username'# 再改回去 以免其他用户登录出现错误
        if user is None:
            return render(request,'login.html',{'account_errmsg':'用户名或密码错误'})
        #状态保持
        login(request,user)
        if remembered != 'on':
            request.session.set_expiry(0)#表示会话结束后就过期
        #重定向到指定页
        return http.HttpResponse('登录成功,来到首页')
