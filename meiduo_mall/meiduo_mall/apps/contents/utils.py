from goods.models import GoodsChannel


def get_categories():
    # 定义用来包装所有广告数据的大字典
    categories = {}

    # 查询出所有频道数据 并且进行排序
    goods_channels_qs = GoodsChannel.objects.order_by('group_id', 'sequence')
    # 遍历商品频道查询集
    for goods_channel in goods_channels_qs:
        # 获取组号
        group_id = goods_channel.group_id
        # 判断当前组数据最初格式是否已经准备过
        if group_id not in categories:  # 若当前组号在字典的key中不存在时，再去添加数据格式
            categories[group_id] = {'channels': [], 'sub_cats': []}

        cat1 = goods_channel.category  # 获取一组模型对象
        # 多给一级类型添加url属性
        cat1.url = goods_channel.url
        # 添加一级数据
        categories[group_id]['channels'].append(cat1)

        # 获取出一级下面的所有二级
        cat2_qs = cat1.subs.all()
        for cat2 in cat2_qs:
            # 把二级下面的三级全部拿到
            cat3_qs = cat2.subs.all()
            # 给每个二级多定义一个sub_cats属性用来保存它自己所有的三级
            cat2.sub_cats = cat3_qs
            # 添加当前组中的每一个二级
            categories[group_id]['sub_cats'].append(cat2)
    return categories