from django.contrib.auth.backends import ModelBackend
import re
from .models import User
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,BadData


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

        # user = get_user_by_account(username)
        # #判断用户密码是否正确
        # if user and user.check_password(password):
        #
        #     #返回user对象
        #     return user



        try:

            user = User.objects.get(username=username)
        except:
            # 如果未查到数据，则返回None，用于后续判断
            try:
                user = User.objects.get(mobile=username)
            except:
                return None

        # 后台管理站点登陆的时候，不会传入request
        if not request and not user.is_staff:
            return None


        # 判断密码
        if user.check_password(password):
            return user
        else:
            return None


def generate_verify_email_url(user):
    """生成用户激活邮箱url"""
    serializer = Serializer(settings.SECRET_KEY,3600*24)
    data = {'user_id':user.id,'email':user.email}
    token = serializer.dumps(data).decode()
    verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token
    return verify_url


def check_verify_email_token(token):
    """传入token后解密后查询用户"""
    serializer = Serializer(settings.SECRET_KEY,3600*24)
    try:
        data = serializer.loads(token)
        user_id = data.get('user_id')
        email = data.get('email')
        try:
            user = User.objects.get(id=user_id,email=email)
            return user
        except User.DoesNotExist:
            return None
    except BadData:
       return None


