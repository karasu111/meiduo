


def jwt_response_payload_handler(token,user=None,request=None):
    '''
    构造jwt默认视图返回数据格式
    :param token: 签发的token
    :param user: 经过身份认证后的用户对象
    :param request: 请求对象
    :return: 返回字典，构建数据
    '''
    return {
        'username':user.username,
        'user_id':user.id,
        'token':token
    }