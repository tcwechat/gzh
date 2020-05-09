

import os

# #腾讯对象存储
# TX_SECRET_ID = os.getenv("TX_SECRET_ID",None)
# TX_SECRET_KEY = os.getenv("TX_SECRET_KEY",None)


import os

BASEURL = os.getenv("BASEURL","http://localhost:9006")
VERSION = os.getenv("VERSION","v1")
APIURL = "{}/{}{}".format(BASEURL,VERSION,"/api")
CALLBACKURL = "{}{}".format(APIURL,"/order/txPayCallback")

#小程序
WECHAT_APPID = os.getenv("WECHAT_APPID","wx6f3ddfe659c7b51f")
WECHAT_SECRET = os.getenv("WECHAT_SECRET","1c1b4c3693011d878a732dffe13222d0")
WECHAT_PAY_MCHID = os.getenv("WECHAT_PAY_MCHID",None)
WECHAT_PAY_KEY = os.getenv("WECHAT_PAY_KEY",None)
WECHAT_PAY_RETURN_KEY = os.getenv("WECHAT_PAY_RETURN_KEY",None)
