from django.contrib.auth.backends import ModelBackend
import re
from users.models import User

class MeiduoModelBackend(ModelBackend):
    def authenticate(self,request,username=None,password=None,**kwargs):
        #判断是否通过vue组件发送请求
        if request is None:
            pass