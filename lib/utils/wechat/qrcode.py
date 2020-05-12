
import json
from requests import request

from lib.utils.wechat.base import WechatBaseForUser
from lib.utils.exceptions import PubErrorCustom


class WechatQrcode(WechatBaseForUser):

    def __init__(self,**kwargs):

        accid = kwargs.get("accid",None)
        if not accid:
            raise PubErrorCustom("accid为空!")

        super().__init__(accid=accid)

    def qrcode_create(self):
        """
        生成临时二维码
        :return:
        """
        response = request(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={}".format(
                               self.auth_accesstoken),
                           json={
                               "expire_seconds": 2592000,
                               "action_name":"QR_SCENE",
                               "action_info": {"scene": {"scene_id": 1}}
                           })
        print(response.text)
        response = json.loads(response.content.decode('utf-8'))
        return response['url']

