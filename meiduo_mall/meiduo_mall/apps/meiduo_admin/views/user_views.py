
from rest_framework.generics import ListAPIView,CreateAPIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination,LimitOffsetPagination

from users.models import User
from meiduo_admin.serializers.user_serializer import UserDetailSerializer
from meiduo_admin.pages import MyPage

# class UserAPIView(GenericAPIView):
class UserAPIView(ListAPIView,CreateAPIView):
    #超级管理员
    queryset = User.objects.filter(is_staff=True)
    serializer_class = UserDetailSerializer
    #指明当前用的分页器
    pagination_class = MyPage

    def get_queryset(self):
        #如果前端传来了keyword,我就过滤
        #否则默认返回默认的所有的数据集

        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(username__contains=keyword).order_by('id') #返回时进行排序 不然会报警告..
        #.all():使用QuerySet集合的缓存
        return self.queryset.all().order_by('id') #返回时进行排序 不然会报警告..

    # def get(self,request):
    #     #1 获得数据集
    #     admin_users = self.get_queryset()
    #     #2 序列化
    #     # serializer = self.get_serializer(admin_users,many=True)
    #     #3 返回
    #     # return Response(serializer.data)
    #
    #     #对admin_users数据进行分页
    #     #默认会在字符串参数中提取page和oagesuze进行分页
    #     page = self.paginate_queryset(admin_users)
    #     if page:
    #         #需要对page该user子集进行序列化返回
    #         serializer = self.get_serializer(page,many=True)
    #
    #         #传入分页后的子集的序列化结果,返回的是分页返回响应对象
    #         return self.get_paginated_response(serializer.data)
    #
    #     #如果没有采用分页器,默认返回所有数据
    #     serializer = self.get_serializer(admin_users,many=True)
    #     return Response(serializer.data)

