from django.contrib.auth.backends import ModelBackend
import re
from .models import User


def get_user_by_account(account):
    """传入用户名或手机号来查询对应的user"""
    try:
        # 判断账号是用户名还是手机号
        if re.match(r'^1[3-9]\d{9}$', account):

            # 若是手机号 就用mobile
            user = User.objects.get(mobile=account)
        else:
            # 若不是就用username
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    return user

class UsernameMobileAuthBackend(ModelBackend):
    """自定义认证类 实现多账号登录"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        # try:
        #     #判断账号是用户名还是手机号
        #     if re.match(r'^1[3-9]\d{9}$',username):
        #
        #         #若是手机号 就用mobile
        #         user = User.objects.get(mobile=username)
        #     else:
        #         #若不是就用username
        #         user = User.objects.get(username=username)
        # except User.DoesNotExist:
        #     return None

        user = get_user_by_account(username)
        #判断用户密码是否正确
        if user and user.check_password(password):

            #返回user对象
            return user