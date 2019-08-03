import json
from decimal import Decimal
from django.utils import timezone
from django import http
from django.shortcuts import render
from meiduo_mall.utils.views import LoginRequiredView
from users.models import Address
from django_redis import get_redis_connection
from goods.models import SKU
from .models import OrderInfo,OrderGoods
from meiduo_mall.utils.response_code import RETCODE
from django.db import transaction
class OrderSettlementView(LoginRequiredView):
    """去结算"""
    def get(self,request):
        user = request.user
        # 查询当前登录用户的所有未被逻辑删除的收货地址
        addresses = Address.objects.filter(user=user,is_deleted=False)

        #创建redis连接对象
        redis_conn = get_redis_connection('carts')
        #获取hash数据
        redis_cart = redis_conn.hgetall('carts_%s'%user.id)
        #获取set数据
        selected_ids = redis_conn.smembers('selected_%s'%user.id)
        cart_dict = {}

        #对hash数据进行过滤只要那些勾选商品的id和count
        for sku_id_bytes in selected_ids:
            cart_dict[int(sku_id_bytes)] = int(redis_cart[sku_id_bytes])

        #通过sku_id查询到所有sku模型
        skus = SKU.objects.filter(id__in=cart_dict.keys())
        #定义一个商品总数量，一个总价
        total_count = 0
        total_amount = 0
        #遍历sku，给每一个sku多定义一个count和amount属性
        for sku in skus:
            sku.count = cart_dict[sku.id]
            sku.amount = sku.count * sku.price


            total_count += sku.count
            total_amount += sku.amount

        freight = Decimal('10.00')

        #包装要进行渲染的数据
        context = {
            'addresses': addresses,#收货地址
            'skus':skus,#所有勾选商品
            'total_count':total_count,#商品总数量
            'total_amount':total_amount,#商品总价
            'freight':freight,#运费
            'payment_amount':total_amount + freight, #实付总金额

        }

        return render(request,'place_order.html',context)


class OrderCommitView(LoginRequiredView):
    """提交订单"""
    def post(self,request):
        #接收请求体数据
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')
        user = request.user
        #校验
        if all([address_id,pay_method]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            address = Address.objects.get(id=address_id,is_deleted=False)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('无效参数')
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'],OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.HttpResponseForbidden('参数有误')
        #生成订单编号
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d'% user.id

        #判断订单状态
        status = (OrderInfo.ORDER_STATUS_ENUM['UNPAID']
            if (pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY'])
                  else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        )
        #手动开启事务
        with transaction.atomic():
            #创建事务保存点
            save_point1 = transaction.savepoint()
            try:

                #新增订单基本信息记录
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0.00'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=status
                )
                #创建redis连接
                redis_conn = get_redis_connection('carts')
                #获取hash数据
                redis_carts = redis_conn.hgetall('carts_%s'%user.id)
                #获取set数据
                selected_ids = redis_conn.smembers('selected_%s'%user.id)
                # 定义字典用来装所有要购买商品id和count
                cart_dict ={}
                # 对redis 中hash购物车数据进行过滤,只要勾选的数据
                for sku_id_bytes in selected_ids:
                    cart_dict[int(sku_id_bytes)] = int(redis_carts[sku_id_bytes])
                #遍历要购买商品数据字典
                for sku_id in cart_dict:
                    while True:
                        #查询sku模型
                        sku = SKU.objects.get(id=sku_id)
                        # 获取当前商品要购买的数量
                        buy_count = cart_dict[sku_id]
                        # 获取当前sku原本的库存
                        origin_stock = sku.stock
                        # 获取当前sku原本销量
                        origin_sales = sku.sales
                        #判断库存
                        if buy_count > origin_stock:
                            #库存不足对事务中的操作进行回滚
                            transaction.savepoint_rollback(save_point1)
                            return http.JsonResponse({'code':RETCODE.STOCKERR,'errmsg':'库存不足'})
                        #修改sku的库存和销量
                        new_stock = origin_stock -buy_count
                        new_sales = origin_sales +buy_count
                        #给sku的库存和销量重新赋值
                        # sku.stock = new_stock
                        # sku.sales = new_sales
                        # sku.save()
                        result = SKU.objects.filter(id=sku_id,stock=origin_stock).update(stock=new_stock,sales=new_sales)
                        if result == 0:
                            continue

                        #修改spu销量
                        spu = sku.spu
                        spu.sales += buy_count
                        spu.save()

                        #新增订单中N个商品记录
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=buy_count,
                            price=sku.price
                        )
                        #累加订单中商品总数量
                        order.total_count += buy_count
                        order.total_amount += (sku.price * buy_count)
                        break  # 当前商品下单成功结束死循环,继续对下一个商品下单
                # 累加运费一定要写在for的外面
                order.total_amount += order.freight
                order.save()
            #try中任务出现问题，暴力回滚
            except Exception:
                transaction.savepoint_rollback(save_point1)
                return http.JsonResponse({'code':RETCODE.STOCKERR,'errmsg':'提交订单失败'})
            else:
                #提交事务
                transaction.savepoint_commit(save_point1)
        #清除购物车中已经购买的商品
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s'%user.id, *cart_dict.keys())
        pl.delete('selected_%s'%user.id)
        pl.execute()
        #响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'order_id': order_id})


class OrderSuccessView(LoginRequiredView):
    def get(self,request):
        #获取查询参数
        query_dict = request.GET
        order_id = query_dict.get('order_id')
        payment_amount = query_dict.get('payment_amount')
        pay_method = query_dict.get('pay_method')

        #校验
        try:
            OrderInfo.objects.get(order_id=order_id,total_amount=payment_amount,pay_method=pay_method)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单有误')


        #包装要进行渲染的数据
        context = {
            'order_id':order_id,
            'payment_amount':payment_amount,
            'pay_method':pay_method
        }

        return render(request,'order_success.html',context)


class OrderCommentView(LoginRequiredView):
    """订单评价"""
    def get(self,request):
        # 查询登录用户
        user = request.user
        #接收订单编号
        order_id = request.GET.get('order_id')
        skus = []
        #查询订单商品列表
        try:
            order_goods = OrderInfo.objects.get(order_id= order_id,user_id=user.id)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('商品编号有误')

        #获取订单中的所有未评价商品
        order_good = order_goods.skus.filter(is_commented=False)

        for sku in order_good:
            sku.display_score = sku.score * 20
            skus.append({
                'default_image_url': sku.sku.default_image.url,
                'name': sku.sku.name,
                'price': str(sku.price),
                'order_id':order_id,
                'sku_id':sku.sku_id
            })
        #包装需要渲染的数据
        context = {
            'uncomment_goods_list':skus
        }

        return render(request,'goods_judge.html',context)


    def post(self,request):

        #接收请求体参数
        json_dict = json.loads(request.body.decode())
        order_id = json_dict.get('order_id')
        sku_id = json_dict.get('sku_id')
        score = json_dict.get('score')
        comment = json_dict.get('comment')
        is_anonymous = json_dict.get('is_anonymous')
        #校验
        if all([score,comment]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        #获取订单中的商品
        try:
            order_goods = OrderGoods.objects.filter(order_id=order_id,sku_id=sku_id)
        except Exception:

            return http.HttpResponseForbidden('无效订单')
        #定义商品信息

        for sku in order_goods:
            sku.comment = comment
            sku.score = score
            sku.is_anonymous = is_anonymous
            sku.save()
        #修改订单状态

        order_info = OrderInfo.objects.get(order_id=order_id)
        order_info.status = OrderInfo.ORDER_STATUS_ENUM['FINISHED']
        order_info.save()

        #修改评价数
        try:
            sku_comment = SKU.objects.get(id=sku_id)
            sku_comment.comments += 1
            sku_comment.save()

            spu_comment = sku_comment.spu
            spu_comment.comments += 1
            spu_comment.save()
        except Exception as e:
            return http.HttpResponseForbidden('无效评价')



        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '评价成功'})






