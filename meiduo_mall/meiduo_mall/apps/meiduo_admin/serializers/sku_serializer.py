

from rest_framework import serializers
from goods.models import SKU,SKUSpecification,GoodsCategory,SPU,\
    SPUSpecification,SpecificationOption


class SKUSpecSimpleSerializer(serializers.ModelSerializer):
    #因为是隐式id不会自动搞过来所以要声明
    spec_id = serializers.IntegerField()
    option_id = serializers.IntegerField()
    class Meta:
        model = SKUSpecification
        fields = ['spec_id','option_id']

class SKUModelSerializer(serializers.ModelSerializer):
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()
    category = serializers.StringRelatedField()
    category_id = serializers.IntegerField()

    #代表的就是与当前sku主表对象关联的多个从表(SKUSpecification)对象集(多个)
    specs = SKUSpecSimpleSerializer(many=True)

    class Meta:
        model = SKU
        fields = '__all__'

    def create(self, validated_data):
        # [{"spec_id":6, "option_id":13} .... ]
        specs = validated_data.pop('specs')

        # 后续在新建sku对象的时候，就会把规格和选项信息丢失
        sku = super().create(validated_data)

        # 根据specs构建中间表数据，来保存新建sku对象的规格和选项信息
        # sku_id=sku.id, spec_id, option_id
        for spec in specs:
            # spec:  {"spec_id":6, "option_id":13}
            # sku_id = sku.id, spec_id = 6, option_id = 13
            # SKUSpecification.objects.create(sku_id=sku.id,
            #                                 spec_id=spec['spec_id'],
            #                                 option_id=spec['option_id'])

            spec['sku_id'] = sku.id
            # 新建中间表数据
            SKUSpecification.objects.create(**spec)

        return sku

    def update(self, instance, validated_data):
        specs = validated_data.pop('specs')

        #有效数据中,忽略了中间表数据
        sku = super().update(instance,validated_data)
        #1 删除原来的中间表数据
        SKUSpecification.objects.filter(sku_id=sku.id).delete()
        #2 根据specs构建新的中间表数据
        for spec in specs:
            # spec:  {"spec_id":6, "option_id":13}
            # sku_id = sku.id, spec_id = 6, option_id = 13
            # SKUSpecification.objects.create(sku_id=sku.id,
            #                                 spec_id=spec['spec_id'],
            #                                 option_id=spec['option_id'])

            spec['sku_id'] = sku.id
            # 新建中间表数据
            SKUSpecification.objects.create(**spec)


        #有效数据中,忽略 中间表数据
        return sku


class SKUCategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = ['id','name']

class SPUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        fields = ['id','name']



#自定义序列化器,序列化选项表读西iang,id和value
class SpecOptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationOption
        fields = ['id','value']

class SPUSpecSerializer(serializers.ModelSerializer):
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()

    #当前SPU规格表对象,关联的多个选项表对象(数据集)
    options = SpecOptSerializer(many=True)

    class Meta:
        model = SPUSpecification
        fields = [
            'id',
            'name',
            'spu',
            'spu_id',
            'options'
        ]