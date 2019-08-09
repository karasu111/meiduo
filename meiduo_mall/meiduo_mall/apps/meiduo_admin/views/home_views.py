from django.conf import settings
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from datetime import timedelta #时间段
from rest_framework.permissions import IsAdminUser, AllowAny

from goods.models import GoodsVisitCount
from meiduo_admin.serializers.home_serializer import *
from users.models import User
from django.utils import timezone
from orders.models import OrderInfo

import pytz

class HomeView(ViewSet):
    #考虑到有降权的业务需求时才用得到这个(在用户有token的情况下失去管理员身份,禁止访问数据)
    # permission_classes = [IsAdminUser]

    #重写函数,实现对特定借口的权限限制
    # def get_permissions(self):
    #     '''
    #     处理的视图函数时totoal_count时,所用的权限检查类对象时IsAdminUser
    #     别的视图处理函数,所使用的权限检查类对象时AllowAny
    #     :return:
    #     '''
    #     # if 视图方法时total_count:
    #     #     返回[IsAdminUser()]
    #     # 返回[AllowAny()]
    #
    #     # self.action代表的是当前请求,视图对象所采用的视图方法
    #     if self.action == 'total_count':
    #         return [IsAdminUser()] #后续权限校验,会依次提取该列表中的权限检查对象,进行检查
    #     return [AllowAny]
    #
    @action(methods=['get'],detail=False)
    def total_count(self,reuquest):
        #统计用户数据
        #1计算用户数量和日期
        count = User.objects.count()
        date = timezone.now().date()  #.now 有十分秒， .date 只有年月日
        #2构建响应数据
        return Response({
            'count':count,
            'date':date
        })


    @action(methods=['get'],detail=False)
    def day_increment(self,request):
        #统计当天日增用户
        #用户新建的日期，大于‘当日’零点零分零秒
        #就是当日新增

        #1获取当日的零时
        #时间类：年 月 日 时 分 秒 时区
        cur_date = timezone.now()
        shanghai_date = cur_date.astimezone(tz=pytz.timezone(settings.TIME_ZONE)) #用pytz搞一个本时区的对象

        #上海的零时
        shanghai_0_date = shanghai_date.replace(hour=0,minute=0,second=0,microsecond=0)

        #2根据当日零时 过滤用户表
        count = User.objects.filter(date_joined__gte=shanghai_0_date).count()

        return Response({
            'count':count,
            'date':shanghai_0_date.date()
        })
    @action(methods=['get'],detail=False)
    def day_active(self,request):
        #1 获取当日零点
        local_0_time = timezone.now().astimezone(tz=pytz.timezone(settings.TIME_ZONE))\
            .replace(hour=0,minute=0,second=0,microsecond=0)
        #2 过滤最后登录日期大于等于当日零点
        count = User.objects.filter(last_login__gte=local_0_time).count()

        #3 返回
        return Response({
            'count':count,
            'date':local_0_time.date() #把十分秒去掉
        })
    @action(methods=['get'],detail=False)
    def day_orders(self,request):
        #统计今天下单的用户
        #已知条件：今天的零点（订单的创建时间） --> 从表的已知条件
        #目标数据：用户数量 --> 主表数据




        #1 统计出今天下的订单
        local_0_time = timezone.now().astimezone(tz=pytz.timezone(settings.TIME_ZONE))\
            .replace(hour=0,minute=0,second=0,microsecond=0)
        #从从表入手
        # 2.1 找出今天下的订单中所有用户个数
        # order_queryset = OrderInfo.objects.filter(create_time__gte=local_0_time)
        #2.2取出每一个从表对象关联的主表，并统计主表数据
        # user_list = []
        # for order in order_queryset:
        #     #order是单一的订单对象
        #     user_list.append(order.user)
        #
        # count = len(set(user_list)) #集合自带去重功能


        #从主表入手
        user_queryset = User.objects.filter(orders__create_time__gte=local_0_time)
        count = len(set(user_queryset))
        # #3 返回
        return Response({
            'count':count,
            'date':local_0_time.date()
        })

    @action(methods=['get'],detail=False)
    def month_increment(self,request):
        #统计最近30天,每一天新增用户

        #1 结束的时间点
        cur_0_time = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE))\
            .replace(hour=0,second=0,minute=0,microsecond=0)
        #2 起始的时间点
        #起始时间点 = 当天的时间点 - (统计天数 - 一天)
        begin_0_time = cur_0_time - timedelta(days=29)

        calc_list = []
        for index in range(30):
            # calc_0_time：30天中的某一天
            calc_0_time = begin_0_time + timedelta(days=index)

            count = User.objects.filter(date_joined__gte=calc_0_time,
                                        date_joined__lt=calc_0_time+timedelta(days=1)).count()

            calc_list.append({
                'count':count,
                'date':calc_0_time.date()
            })
        return Response(calc_list)

class GoodsVisitCountView(ListAPIView):
    permission_classes = [IsAdminUser]

    queryser = GoodsVisitCount.objects.all()
    serializer_class = GoodsVisitCountSerializer

    def get_queryset(self):
        cur_0_time = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE))\
            .replace(hour=0,second=0,minute=0,microsecond=0)
        return self.queryser.filter(create_time__gte=cur_0_time)