

#定义一个序列化器,对User进行序列化操作
from rest_framework import serializers
from users.models import User
#django提供的密码加密,提供明文密码返回密文密码 通过哈希操作 不可逆 都是加密后比对
from django.contrib.auth.hashers import make_password

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', # read_only=True
            'username',
            'mobile',
            'email',

            'password'
        ]

        extra_kwargs = {
            'password':{'write_only':True}
        } #password仅作用于反序列化校验

    def create(self,validated_data):
        '''
        新建用户的时和,1 密码加密 2 超级管理员
        :param validated_data:
        :return: 用户对象
        '''

        # password = validated_data['password'] #明文
        # # validated_data['password'] = 密文
        # validated_data['password'] = make_password(password)
        # validated_data['is_staff'] = True
        # #有效数据中:1 明文改密文 2 添加超级管理员权限
        # return super().create(validated_data)
        #========================================方法2
        # return User.objects.create_superuser(**validated_data)
        #========================================方法3
        return self.Meta.model.objects.create_superuser(**validated_data)

