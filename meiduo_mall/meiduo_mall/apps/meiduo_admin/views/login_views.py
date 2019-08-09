
from rest_framework.views import APIView
from meiduo_admin.serializers.login_serializer import LoginSerializer
from rest_framework.response import Response
#定义类视图，处理登录请求，调用序列化器完成用户和token签发

class LoginView(APIView):

    def post(self,request):
        #1 调用序列化器完成数据校验
        serializer = LoginSerializer(data=request.data)
        #1.1 启动校验流程
        serializer.is_valid(raise_exception=True)
        #2 构建返回数据
        return Response(data={
            'username':serializer.validated_data['user'].username,
            'user_id':serializer.validated_data['user'].id,
            'token':serializer.validated_data['token'],
        })
