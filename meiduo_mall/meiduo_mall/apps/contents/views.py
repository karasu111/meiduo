from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View
from goods.models import GoodsCategory,GoodsChannel
from .utils import get_categories
from .models import Content,ContentCategory


class IndexView(View):
    """首页广告"""
    def get(self,request):
        #定义用来包装所有广告数据的大字典
        contents = {}
        #查询所有广告类别
        content_cat_qs = ContentCategory.objects.all()
        for content_cat in content_cat_qs:
            contents[content_cat.key] = content_cat.content_set.filter(status=True).order_by('sequence')


        context = {
            'categories':get_categories(),
            'contents': contents
        }
        return render(request,'index.html',context)

