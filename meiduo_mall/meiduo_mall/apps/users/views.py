import re
from .models import User
from django import http
from django.shortcuts import render
from django.views import View
from django.contrib.auth import login
from meiduo_mall.utils.response_code import RETCODE
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
        sms_code = query_dict.get('sms_code')
        allow = query_dict.get('allow')
        """校验"""
        if not all([username,password,password2,mobile,sms_code,allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        if password != password2:
            return http.HttpResponseForbidden('两次密码输入的不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        #TODO: 短信验证码后期补充

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