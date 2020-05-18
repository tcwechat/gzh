
import json
from requests import request

from lib.utils.wechat.base import WechatBaseForUser
from lib.utils.exceptions import PubErrorCustom

from app.public.models import Meterial
from django.shortcuts import HttpResponse

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

    def type_change(self,type):
        if type == '2':
            return 'image'
        elif type == '4':
            return 'voice'
        elif type == '5':
            return 'video'
        elif type =='6':
            return 'thumb'
        else:
            raise PubErrorCustom("类型有误!")


    def create_forever(self,**kwargs):

        meterialObj = kwargs.get("meterialObj",None)
        type = self.type_change(kwargs.get("type",None))
        title = kwargs.get("title",None)
        introduction = kwargs.get("introduction",None)



        response = request(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={}&type={}".format(
                               self.auth_accesstoken,type),
                           files={"media":(meterialObj['filename'],meterialObj['file'])},
                           json={} if type !='video' else {
                               "description":{
                                   "title": title if title else "title",
                                   "introduction": introduction if introduction else "introduction"
                               }
                           })
        print(response.text)
        response = json.loads(response.content.decode('utf-8'))

        media_id = response['media_id']
        url = response.get("url","")

        return media_id,url


    def delete_forever(self,media_id):

        response = request(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/material/del_material?access_token={}".format(
                               self.auth_accesstoken),
                           json={
                                "media_id":media_id
                           })
        response = json.loads(response.content.decode('utf-8'))
        if str(response['errcode']) != '0':
            raise PubErrorCustom(response['errmsg'])

    def get_forever(self,id):


        try:
            obj = Meterial.objects.get(id=id)
        except Meterial.DoesNotExist:
            raise PubErrorCustom("不存在此素材!")


        obj.type = self.type_change(obj.type)

        response = request(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/material/get_material?access_token={}".format(
                               self.auth_accesstoken),
                           json={
                                "media_id":obj.media_id
                           })

        if obj.type == 'video':
            response = json.loads(response.content.decode('utf-8'))
            return {"data":response}
        else:
            return HttpResponse(response,"content_type='image/png'")