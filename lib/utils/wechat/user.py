


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

class WeChatAccTag(WechatBase):

    def __init__(self,**kwargs):

        self.auth_accesstoken = kwargs.get("auth_accesstoken",None)
        super().__init__(**kwargs)

    def create(self,name):

        response = self.request_handler(
            method="GET",
            url="https://api.weixin.qq.com/cgi-bin/tags/create?access_token={}".format(
                self.auth_accesstoken
            ),
            json={"tag":{"name":name}})
        return response['id']

    def update(self,id,name):

        self.request_handler(
            method="GET",
            url="https://api.weixin.qq.com/cgi-bin/tags/update?access_token={}".format(
                self.auth_accesstoken
            ),
            json={"tag":{"id":id,"name":name}})

    def delete(self,id):

        self.request_handler(
            method="GET",
            url="https://api.weixin.qq.com/cgi-bin/tags/delete?access_token={}".format(
                self.auth_accesstoken
            ),
            json={"tag":{"id":id}})