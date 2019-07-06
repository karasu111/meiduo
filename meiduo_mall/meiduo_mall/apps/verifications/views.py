from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django import http
from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.utils.response_code import RETCODE

# Create your views here.
class ImageCodeView(View):
    def get(self,request,uuid):
        name,text,image_bytes = captcha.generate_captcha()

        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex(uuid,300,text)
        return http.HttpResponse(image_bytes,content_type='image/png')


class SMSCodeView(View):
    """发送短信验证码"""
    def get(self,request,moile):
        #接受前端数据
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        #校验
        if all([image_code_client,uuid]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        #创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        #获取redis中图形验证码
        image_code_server = redis_conn.get(uuid)
        #判断图形验证码是否过期
        if image_code_server is None:
            return http.JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图形验证码过期'})
        #判断用户输入的图形验证码和redis中之前存储的验证码是否一致
        if image_code_client.lower() != image_code_server.decode().lower():
            return http.JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图形验证码输入错误'})

        pass

