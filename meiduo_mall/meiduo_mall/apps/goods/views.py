from datetime import date

from django.shortcuts import render
from contents.utils import get_categories
from .models import GoodsCategory,SKU,GoodsVisitCount
from django import http
from .utils import get_breadcrumb
from django.core.paginator import Paginator,EmptyPage
from meiduo_mall.utils.response_code import RETCODE
from django.utils import timezone

# Create your views here.
from django.views.generic.base import View


class ListView(View):
    """商品列表界面"""
    def get(self,request,category_id,page_num):
        #提供商品列表页
        #判断category_id是否存在
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')
        #接收前端传入的sort='xxx'
        sort = request.GET.get('sort','default')
        #按照排序规则查询该分类商品的SKU
        if sort == 'price':
            sort_field = 'price'
        elif sort == 'hot':
            sort_field = '-sales'
        else:
            sort = 'default'
            sort_field = 'create_time'

         #分页
        #把当前三级类型下的所有上架的sku拿到
        sku_qs = category.sku_set.filter(is_launched=True).order_by(sort_field)
        # 创建分页器 Paginator(要进行分页的所有数据, 指定每页显示多少条数据)
        paginator = Paginator(sku_qs,5)
        try:
            # 获取每页商品数据
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return http.HttpResponseForbidden('非法请求 没有指定页面')
        #获取列表总页数
        total_page = paginator.num_pages





        context = {
            #查询商品分类
            'categories': get_categories(),
            #查询面包屑导航
            'breadcrumb': get_breadcrumb(category),
            #排序
            'sort':sort,
            #第三级分类
            'category': category,
            #分页后数据
            'page_skus': page_skus,
            #总页数
            'total_page': total_page,
            #当前页码
            'page_num': page_num,

        }
        return render(request,'list.html',context)


class HotGoodsView(View):
    """获取热销商品"""
    def get(self,request,category_id):
        # 判断category_id是否存在
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')

        # 查询当前指定三级类别中销量最高的前两个商品
        sku_qs = category.sku_set.filter(is_launched=True).order_by('-sales')[:2]

        #模型转字典
        hot_skus = []
        for sku in sku_qs:
            hot_skus.append({
                'id':sku.id,
                'name':sku.name,
                'price':sku.price,
                'default_image_url':sku.default_image.url
            })
        #响应
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK','hot_skus':hot_skus})


class DetailView(View):

    def get(self, request, sku_id):

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        category = sku.category  # 获取当前sku所对应的三级分类

        # 查询当前sku所对应的spu
        spu = sku.spu

        """1.准备当前商品的规格选项列表 [8, 11]"""
        # 获取出当前正显示的sku商品的规格选项id列表
        current_sku_spec_qs = sku.specs.order_by('spec_id')
        current_sku_option_ids = []  # [8, 11]
        for current_sku_spec in current_sku_spec_qs:
            current_sku_option_ids.append(current_sku_spec.option_id)

        """2.构造规格选择仓库
        {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        """
        # 构造规格选择仓库
        temp_sku_qs = spu.sku_set.all()  # 获取当前spu下的所有sku
        # 选项仓库大字典
        spec_sku_map = {}  # {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        for temp_sku in temp_sku_qs:
            # 查询每一个sku的规格数据
            temp_spec_qs = temp_sku.specs.order_by('spec_id')
            temp_sku_option_ids = []  # 用来包装每个sku的选项值
            for temp_spec in temp_spec_qs:
                temp_sku_option_ids.append(temp_spec.option_id)
            spec_sku_map[tuple(temp_sku_option_ids)] = temp_sku.id

        """3.组合 并找到sku_id 绑定"""
        spu_spec_qs = spu.specs.order_by('id')  # 获取当前spu中的所有规格

        for index, spec in enumerate(spu_spec_qs):  # 遍历当前所有的规格
            spec_option_qs = spec.options.all()  # 获取当前规格中的所有选项
            temp_option_ids = current_sku_option_ids[:]  # 复制一个新的当前显示商品的规格选项列表
            for option in spec_option_qs:  # 遍历当前规格下的所有选项
                temp_option_ids[index] = option.id  # [8, 12]
                option.sku_id = spec_sku_map.get(tuple(temp_option_ids))  # 给每个选项对象绑定下他sku_id属性

            spec.spec_options = spec_option_qs  # 把规格下的所有选项绑定到规格对象的spec_options属性上

        context = {
            'categories': get_categories(),  # 商品分类
            'breadcrumb': get_breadcrumb(category),  # 面包屑导航
            'sku': sku,  # 当前要显示的sku模型对象
            'category': category,  # 当前的显示sku所属的三级类别
            'spu': spu,  # sku所属的spu
            'spec_qs': spu_spec_qs,  # 当前商品的所有规格数据
        }
        return render(request, 'detail.html', context)


class DetailVisitView(View):
    """详情页分类商品访问量"""
    def post(self,request,category_id):
        # 判断category_id是否存在
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')
        # now_date = timezone.localtime()  # 获取当前日期对象
        #获取当前时间日期对象
        now_date = timezone.now()

        # 查询当天有没有访问过此类别商品
        try:
            goods_visit = GoodsVisitCount.objects.get(date=now_date,category=category)
        except GoodsVisitCount.DoesNotExist:
            # 如果此三级类型今天是第一次访问就新增一条访问记录
            goods_visit = GoodsVisitCount(
                category=category
            )
        #无论有无都累加1次
        goods_visit.count += 1
        goods_visit.save()

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})
#=============================================================================
    #教员的
    # def post(self, request, category_id):
    #     try:
    #         gvc = GoodsVisitCount.objects.get(category_id=category_id)
    #     except:
    #         GoodsVisitCount.objects.create(
    #             category_id=category_id,
    #             count=1
    #         )
    #     else:
    #         if gvc.create_time.date() == timezone.now().date():
    #             gvc.count += 1
    #             gvc.date = date.today()
    #             gvc.save()
    #         else:
    #             gvc.delete()
    #             GoodsVisitCount.objects.create(
    #                 category_id=category_id,
    #                 count=1
    #             )
    #     return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
