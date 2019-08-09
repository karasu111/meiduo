

from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from goods.models import SKU, SPU,SPUSpecification
from meiduo_admin.serializers.sku_serializer import *
from meiduo_admin.pages import MyPage
from goods.models import GoodsCategory

class SKUViewSet(ModelViewSet):
    queryset = SKU.objects.all()
    serializer_class = SKUModelSerializer
    pagination_class = MyPage
    #查询(重写get_queryset方法,判断是否传递keyword查询参数
    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(name__contains=keyword)
        return self.queryset.all()

class SKUCategoryView(ListAPIView):
    queryset = GoodsCategory.objects.filter(parent_id__gt=37)
    serializer_class = SKUCategorySimpleSerializer

class SPUSimpleView(ListAPIView):
    queryset = SPU.objects.all()
    serializer_class = SPUSimpleSerializer



class SPUSpecView(ListAPIView):
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecSerializer

    def get_queryset(self):
        #根据前端传来的spu_id过滤出该spu关联的规格对象
        spu_id = self.kwargs.get('pk')
        if spu_id:
            return self.queryset.filter(spu_id=spu_id)
        return self.queryset.all()