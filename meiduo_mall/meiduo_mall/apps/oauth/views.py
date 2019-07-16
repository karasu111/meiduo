from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic.base import View
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django import http
from meiduo_mall.utils.response_code import RETCODE
from .models import OAuthQQUser
from django.contrib.auth import login
import re
from django_redis import get_redis_connection
from .utils import generate_openid_signature,check_openid_signature
import logging
logger = logging.getLogger('django')
class OAuthURLView(View):
    """提供QQ登录界面链接"""
    def get(self,request):
        next = request.GET.get('next','/')#表示从哪个页面进入到的登录页面 将来登录成功后 就自动回到那个页面
        # QQ_CLIENT_ID = '101518219'
        # QQ_CLIENT_SECRET = '418d84ebdc7241efb79536886ae95224'
        # QQ_REDIRECT_URI = 'http://www.meiduo.site:8000/oauth_callback'

        #获取QQ登录页面网址
        # client_id = 'appid',
        # client_secret = 'app key',
        # redirect_uri = '登录成功后的回调url',
        # state = '记录界面跳转来源'
        oauth = OAuthQQ(
            client_id= settings.QQ_CLIENT_ID,
            client_secret= settings.QQ_CLIENT_SECRET,
            redirect_uri= settings.QQ_REDIRECT_URI,
            state=next#授权成功后会原样返回
        )
        #调用SDK中 get_qq_url方法得到拼接好的qq登录url
        login_url = oauth.get_qq_url()
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK','login_url':login_url})



class OAuthUserView(View):
    """用户扫码登录的回调处理"""
    def get(self,request):
        #获取查询参数中的code
        code = request.GET.get('code')
        #查看是否获取到了
        if code is None:
            return http.HttpResponseForbidden('缺少code')

        #创建OAuthQQ对象
        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,

        )
        try:
            #使用code向QQ服务器请求access_token
            access_token = oauth.get_access_token(code)
            #使用access_token向QQ服务器请求openid
            openid = oauth.get_open_id(access_token)
        except Exception:
            return http.HttpResponseServerError('QQ登录失败')
        #向数据中查询openid，判断openid是否绑定过用户
        try:
            oauth_model = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            #如果查询不到openid说明未绑定用户，把openid和美多用户绑定
            # 包装模板要进行渲染的数据
            context = {
                'openid': generate_openid_signature(openid)#openid是敏感数据 需要加密
            }
            return render(request,'oauth_callback.html',context)
        else:
            #如果已经绑定了，直接代表登陆成功
            #利用外键获取user
            user = oauth_model.user
            #状态保持
            login(request,user)
            #重定向
            response = redirect(request.GET.get('state') or '/')
            #登录时用户名写入到cookie
            response.set_cookie('username',user.username,max_age=settings.SESSION_COOKIE_AGE)
            return response


    def post(self,request):
        """绑定用户的实现"""
        #接收参数
        query_dict =request.POST
        mobile = query_dict.get('mobile')
        password = query_dict.get('password')
        sms_code_client = query_dict.get('sms_code')
        openid = query_dict.get('openid')

        #校验参数
        if not all([password,mobile,sms_code_client]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')



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
        if not openid:
            return render(request,'oauth_callback.html',{'openid_errmsg':'无效的openid'})


        try:
            user = User.objects.get(mobile=mobile)
            if not user.check_password(password):
                return render(request,'oauth_callback.html',{'account_errmsg':'用户名或密码错误'})

        except User.DoesNotExist:
            #用户不存在 新建用户
            user = User.objects.create_user(username=mobile,password=password,mobile=mobile)
        #对openid解密再绑定
        openid = check_openid_signature(openid)
        if openid is None:
            return http.HttpResponseForbidden('openid无效')
        #若能执行到这儿 用户绝对已经有了
        #用户openid和user绑定
        OAuthQQUser.objects.create(user=user,openid=openid)

        login(request,user)
        response = redirect(request.GET.get('state') or '/')
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
        return response










