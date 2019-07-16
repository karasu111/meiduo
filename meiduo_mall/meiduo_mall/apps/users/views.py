import json
import re
from .models import User, Address
from django import http
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login,authenticate,logout
from meiduo_mall.utils.response_code import RETCODE
from django_redis import get_redis_connection
from django.conf import settings
from django.contrib.auth import mixins
from meiduo_mall.utils.views import LoginRequiredView
from celery_tasks.email.tasks import send_verify_email
from .utils import generate_verify_email_url,check_verify_email_token

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
        response = redirect('/')
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
        return response


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

    #多账号登录不推荐版
    # def post(self,request):
    #     #接收前端传入的表单数据
    #     query_dict = request.POST
    #     username = query_dict.get('username')
    #     password = query_dict.get('password')
    #     remembered = query_dict.get('remembered')
    #
    #     #判断用户是否是用手机登录，若是的 认证时 就用手机号查询
    #     if re.match(r'^1[3-9]\d{9}$',username):
    #         User.USERNAME_FIELD = 'mobile'
    #     #校验
    #     user = authenticate(request,username=username,password=password)
    #     User.USERNAME_FIELD = 'username'# 再改回去 以免其他用户登录出现错误
    #     if user is None:
    #         return render(request,'login.html',{'account_errmsg':'用户名或密码错误'})
    #     #状态保持
    #     login(request,user)
    #     if remembered != 'on':
    #         request.session.set_expiry(0)#表示会话结束后就过期
    #     #重定向到指定页
    #     return http.HttpResponse('登录成功,来到首页')
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

        if user is None:
            return render(request,'login.html',{'account_errmsg':'用户名或密码错误'})
        #状态保持
        login(request,user)
        if remembered != 'on':
            request.session.set_expiry(0)#表示会话结束后就过期

        #用户如果有来源就重定向到来源 反之就去首页
        response = redirect(request.GET.get('next') or '/')
        response.set_cookie('username',user.username,max_age=settings.SESSION_COOKIE_AGE if remembered else None)
        print(settings.SESSION_COOKIE_AGE)


        #重定向到指定页
        return response


class LogoutView(View):
    def get(self,requst):
        #清除状态保持
        logout(requst)
        #创建响应对象
        response = redirect('/login/')

        # 重定向到登录界面
        #删除cookie中的username
        response.delete_cookie('username')
        return response





# class InfoView(View):
#     """用户中心"""
#     def get(self,request):
#         # if isinstance(request.user,User):
#         if request.user.is_authenticated:#如果if成立说明是登录用户
#             return render(request,'user_center_info.html')
#         else:
#             return redirect('/login/?next=/info/')


class InfoView(mixins.LoginRequiredMixin,View):
    """用户中心"""
    def get(self,request):

        return render(request,'user_center_info.html')


class EmailView(LoginRequiredView):
    def put(self,request):
        #接收数据
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')
        #校验
        if email is None:
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('邮件格式不正确')
        #获取登录用户
        user = request.user
        #修改email
        User.objects.filter(id=user.id,email='').update(email=email)#邮箱只要设置成功了 此代码将是无效修改
        #发送邮件

        from django.core.mail import send_mail

        # send_mail(subject='主题', message='邮件普通正文', from_email='发件人', recipient_list='收件人,必须是列表',
        #       html_message='超文本的邮件内容')
        # send_mail(subject='主题', message='邮件普通正文', from_email=settings.EMAIL_FROM, recipient_list=[email],
        #       html_message="<a href='http://www.itcast.cn'>'xxxxxx'</a>")
        # verify_url = 'http://www.meiduo.site:8000/emails/verification/?token=3'
        verify_url = generate_verify_email_url(user)
        print(verify_url)
        send_verify_email.delay(email,verify_url)
        #响应添加邮箱结果
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})


class VerifyEmailView(View):
    def get(self,request):
        #获取查询参数中的token
        token = request.GET.get('token')
        #校验
        if token is None:
            return http.HttpResponseForbidden('缺少token')
        user = check_verify_email_token(token)
        # 再对token进行解密,解密后根据里面的user_id,和email查询出要激活邮箱的那个User
        if user is None:
            return http.HttpResponseForbidden('token无效')
        #修改user的email_active字段 设置为True
        user.email_active = True
        user.save()
        #响应
        return redirect('/info/')


class AddressView(LoginRequiredView):
    """收货地址"""
    def get(self,request):
        user = request.user#获取用户
        address_qs = Address.objects.filter(user=user,is_deleted=False)
        address_list = []#用来装用户所有收货地址字典
        #把新增的address模型对象转换成字典 并响应给前端
        for address in address_qs:
            address_dict = {
                'id': address.id,
                'title': address.title,
                'receiver': address.receiver,
                'province_id': address.province_id,
                'province': address.province.name,
                'city_id': address.city_id,
                'city': address.city.name,
                'district_id': address.district_id,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'tel': address.tel,
                'email': address.email,                                                         
            }
            #添加收货地址字典到列表中
            address_list.append(address_dict)
            #包装模板要进行渲染的数据
        context = {
            'addresses':address_list,# 当前登录用户的所有收货地址 [{}, {}]
            'default_address_id':user.default_address_id# 当前用户默认收货地址id

        }
        return render(request,'user_center_site.html',context)


class CreateAddressView(LoginRequiredView):
    """新增收货地址"""
    def post(self,request):
        #判断用户收货地址上限，不能多于20个
        user = request.user
        #计算个数
        count = Address.objects.filter(user=user,is_deleted=False).count()
        if count >=20:
            return http.JsonResponse({'code':RETCODE.MAXNUM,'errmsg':'收货地址超限'})
        #接收请求体数据
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        #校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')


        #新增
        try:
            address = Address.objects.create(
                user=user,
                title=title,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception:
            return http.HttpResponseForbidden('添加收货地址失败')

        #如果用户还没有默认收货地址 把新增的收货地址设置为用户的默认收货地址
        if user.default_address is None:
            user.default_address = address
            user.save()


        #把新增deaddress模型转换成字典 并响应给前端
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email,
        }
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'添加收货地址成功','address':address_dict})


class UpdateDestroyAddressView(LoginRequiredView):
    """修改和删除收货地址"""
    def put(self,request,address_id):
        #获取地址
        address = Address.objects.get(id=address_id,user=request.user,is_deleted=False)
        # 接收请求体数据
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 修改
        try:
            # Address.objects.filter(id=address_id).update(
            #
            #     title=title,
            #     receiver=receiver,
            #     province_id=province_id,
            #     city_id=city_id,
            #     district_id=district_id,
            #     place=place,
            #     mobile=mobile,
            #     tel=tel,
            #     email=email
            # )
            address.title = title
            address.receiver = receiver
            address.province_id = province_id
            address.city_id = city_id
            address.district_id = district_id
            address.place = place
            address.mobile = mobile
            address.tel = tel
            address.email = email
            address.save()
        except Exception:
            return http.HttpResponseForbidden('修改收货地址失败')

            # 把新增deaddress模型转换成字典 并响应给前端
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email,
        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改收货地址成功', 'address': address_dict})


    def delete(self,request,address_id):
        try:
            address = Address.objects.get(id=address_id, user=request.user, is_deleted=False)
        except Exception:
            return http.HttpResponseForbidden('删除收货地址失败')


        address.is_deleted = True
        address.save()
        #物理删除：address.delete()

        # 响应删除地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})



class DefaultAddressView(LoginRequiredView):
    """设置默认地址"""
    def put(self,request,address_id):
        try:
            #获取地址
            address = Address.objects.get(id=address_id,user=request.user,is_deleted=False)
        except Exception:
            return http.HttpResponseForbidden('设置默认地址失败')

        request.user.default_address = address
        request.user.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateTitleAddressView(LoginRequiredView):
    """修改地址标题"""
    def put(self,request,address_id):
        try:
            # 获取地址
            address = Address.objects.get(id=address_id, user=request.user, is_deleted=False)
        except Exception:
            return http.HttpResponseForbidden('修改地址标题失败')

        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        if title is None:
            return http.HttpResponseForbidden('缺少必传参数')

        address.title = title
        address.save()

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'修改地址标题成功'})


class ChangePasswordView(LoginRequiredView):
    """修改密码"""
    def get(self,request):
        """展示修改密码界面"""
        return render(request,'user_center_pass.html')


    def post(self,request):
        query_dict = request.POST
        old_pwd = query_dict.get('old_pwd')
        new_pwd = query_dict.get('new_pwd')
        new_cpwd = query_dict.get('new_cpwd')
        user = request.user
        if all([old_pwd,new_pwd,new_cpwd]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        if user.check_password(old_pwd) is False:
            return render(request,'user_center_pass.html',{'origin_pwd_errmsg': '原始密码不正确'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_pwd):
            return http.HttpResponseForbidden('请输入8-20位长度的密码')
        if new_pwd != new_cpwd:
            return http.HttpResponseForbidden('两次密码输入的不一致')
        user.set_password(new_pwd)
        user.save()

        #重定向到login
        return redirect('/login/')
















