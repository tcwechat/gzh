


from lib.utils.wechat.base import WechatBase



class WechatAccUser(WechatBase):

    def __init__(self,**kwargs):

        self.auth_accesstoken = kwargs.get("auth_accesstoken",None)
        super().__init__(**kwargs)

    def get_info(self,openid):
        return self.request_handler(
            method="GET",
            url="https://api.weixin.qq.com/cgi-bin/user/info?access_token={}&openid={}&lang=zh_CN".format(
                self.auth_accesstoken,
                openid
            ))