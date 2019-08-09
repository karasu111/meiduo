#JWT

import json,base64
#底层用来签名的模块
import hmac,hashlib

#固定的
header = {
    'typ':'JWT',
    'alg':'HS256' #sha256签名算法(不可逆，加密算法）
}

# dict --> json
header = json.dumps(header) #string
# json --> base64
header = base64.b64encode(header.encode()) #bytes
print(header)


payload = {
    'username':'xxxxx',
    'age':17
}
payload = json.dumps(payload)
payload = base64.b64encode(payload.encode())
print(payload)


# msg = header + '.' + payload
# signature = sha256(msg,密钥)
#1,构建加密信息：header+'.'+payload
msg = header + b'.' + payload #在字符串前面加b转换成字节
SECRET_KEY = b'a@70f%=f2j7qf%)84v0fca78h02-lk&0s^hbn82hw68c6t$5yg'
#digestmod指定算法  .hexdigest是把前面变成一长串的字符串
signature = hmac.new(SECRET_KEY, msg, digestmod=hashlib.sha256).hexdigest() #string
print(signature)

JWT_TOKEN = header.decode() + '.' + payload.decode() + '.' +signature
print('JWT_TOKEN:',JWT_TOKEN)


#把token值响应给浏览器

#浏览器在一次访问，携带这样的一个token值
#后端需要对该token值进行校验，判断是否数据篡改

#没有篡改
# jwt_from_browser = JWT_TOKEN
#模拟篡改
jwt_from_browser = 'asdfsa ' +JWT_TOKEN


#验证操作
#1 提取header，payload和signature
header = jwt_from_browser.split('.')[0]
payload = jwt_from_browser.split('.')[1]
signature = jwt_from_browser.split('.')[2]
#2 针对header，payload配合后端密钥再一次加密得到新的new_signature
new_signature = hmac.new(SECRET_KEY,(header+'.'+payload).encode(), digestmod=hashlib.sha256).hexdigest()
#3 对比new_signature和signature,是否一致,如果一致则未篡改,如果不一致说明header或payload信息是被篡改的
if new_signature == signature:
    print('数据是完整的')
else:
    print('数据篡改了')