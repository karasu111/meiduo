from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django import http
from meiduo_mall.libs.captcha.captcha import captcha

# Create your views here.
class ImageCodeView(View):
    def get(self,request,uuid):
        name,text,image_bytes = captcha.generate_captcha()

        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex(uuid,300,text)
        return http.HttpResponse(image_bytes,content_type='image/png')
