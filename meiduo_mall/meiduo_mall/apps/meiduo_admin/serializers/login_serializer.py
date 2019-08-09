
#定义序列化器校验username和password
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_jwt.utils import jwt_encode_handler,jwt_payload_handler

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        #1 校验用户密码，完成传统身份认证
        #username = attrs['username']
        #password = attrs['password']
        #user = authenticate(username=username.password=password)
        user = authenticate(**attrs)

        if not user:
            #用户对象为None，传统身份认证失败
            raise serializers.ValidationError('传统身份认证失败，请检查用户名和密码是否正确')


        #2 校验通过，签发jwt_token
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        #返回的数据是用来生产最终的有效数据的
        return {
            'user':user,
            'token':token
        }