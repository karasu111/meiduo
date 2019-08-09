
#定义一个序列化器,完成对GoodsVisitCount模型类的序列化操作
#category和count两个字段

from rest_framework import serializers
from goods.models import GoodsVisitCount


class GoodsVisitCountSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField() #因为是外键, 过来的时候会是关联的主键ID,所以要自定义返回类型
    class Meta:
        model = GoodsVisitCount
        fields = ['category','count']