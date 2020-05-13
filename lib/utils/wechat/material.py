
import json
from requests import request

from lib.utils.wechat.base import WechatBaseForUser
from lib.utils.exceptions import PubErrorCustom


class WechatMaterial(WechatBaseForUser):

    def __init__(self,**kwargs):

        accid = kwargs.get("accid",None)
        if not accid:
            raise PubErrorCustom("accid为空!")

        super().__init__(accid=accid)

    def get_file_by_url(self,url):

        return None

    # def create_forever(self,**kwargs):
    #
    #     type = kwargs.get("type",None)
    #     picurl = kwargs.get("type",None)
    #     title = kwargs.get("title",None)
    #
    #     if type == '1':
    #         """
    #         图文
    #         """
    #
    #         #上传图文消息内的图片获取URL
    #         response = request(method="POST",
    #                            url="https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={}".format(
    #                                self.auth_accesstoken),
    #                            files=self.get_file_by_url(picurl))
    #
    #         response = json.loads(response.content.decode('utf-8'))
    #         url = response['url']
    #
    #         #新增永久图文素材
    #         response = request(method="POST",
    #                            url="https://api.weixin.qq.com/cgi-bin/material/add_news?access_token={}".format(
    #                                self.auth_accesstoken),
    #                            json={
    #                                 "articles":[
    #                                     {
    #                                         "title":title,
    #
    #                                     }
    #                                 ]
    #                            })

    def create_forever(self,**kwargs):

        meterialObj = kwargs.get("meterialObj",None)
        type = kwargs.get("type",None)
        title = kwargs.get("title",None)
        introduction = kwargs.get("introduction",None)

        if type == '2':
            type = 'image'
        elif type == '4':
            type = 'voice'
        elif type == '5':
            type = 'video'
        elif type =='6':
            type = 'thumb'
        else:
            raise PubErrorCustom("类型有误!")

        response = request(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={}&type={}".format(
                               self.auth_accesstoken,type),
                           files={"media":(meterialObj.name,[chunk for chunk in meterialObj.chunks()])},
                           json={
                                "type":type
                           })
        print(response.text)
        response = json.loads(response.content.decode('utf-8'))

        media_id = response['media_id']
        url = response.get("url","")

        return media_id,url