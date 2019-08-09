
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class MyPage(PageNumberPagination):
    #page_query_param 前端发送的页数关键字名，默认为"page"
    page_query_param = 'page'
    #max_page_size 前端最多能设置的每页数量
    max_page_size = 10
    #page_size_query_param 前端发送的每页数目关键字名，默认为None
    page_size_query_param = 'pagesize'
    #每页数目
    page_size = 5

    def get_paginated_response(self, data):
        '''
        构建响应对象,构建返回对数据格式
        :param data: 分页的子集
        :return: 响应对象
        '''

        return Response({
            'counts':self.page.paginator.count, #总数量 需要分页的总数
            'lists':data,# 用户数据
            'page':self.page.number, #当前页数
            'pages':self.page.paginator.num_pages, #总页数
            'pagesize':self.page_size, #前端传来的页数
        })