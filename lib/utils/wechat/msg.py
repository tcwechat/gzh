
import json,random
from lib.utils.wechat.base import WechatBase
from lib.utils.wechat.WXBizMsgCrypt import WXBizMsgCrypt
from lib.utils.exceptions import PubErrorCustom
import xmltodict
from app.wechat.models import AccQrcode,AccLinkUser,AccQrcodeList
from app.public.models import Meterial


class WechatAccMsg(WechatBase):

    def __init__(self,**kwargs):

        authorizer_appid = kwargs.get("authorizer_appid",None)
        if not authorizer_appid:
            raise PubErrorCustom("authorizer_appid void!")

        super().__init__(isAccessToken=True,authorizer_appid=authorizer_appid)

        res = self.DecryptMsg(
            kwargs.get("timestamp"),
            kwargs.get("nonce"),
            kwargs.get("signature"),
            kwargs.get("xmlc")
        )
        if res[0] != 0:
            raise PubErrorCustom("解密错误!{}".format(res[0]))

        self.xml_data = xmltodict.parse(res[1])['xml']

    def DecryptMsg(self,timestamp,nonce,signature,xmlc):

        return WXBizMsgCrypt(self.token,self.key,self.appid).DecryptMsg(xmlc,signature,timestamp,nonce)

    def EncryptMsg(self):
        pass

    def eventHandler(self):

        print(self.xml_data)

        if self.xml_data['MsgType'] == 'event':
            """
            扫描带参数二维码事件
            """
            if (self.xml_data['Event'] == 'subscribe' and 'EventKey' in self.xml_data) or self.xml_data['Event'] == 'SCAN':

                if self.xml_data['Event'] == 'SCAN':
                    """
                    如果用户已经关注公众号，则微信会将带场景值扫描事件推送给开发者
                    """
                    try:
                        aqc_obj = AccQrcode.objects.select_for_update().get(id=self.xml_data['EventKey'])
                    except AccQrcode.DoesNotExist:
                        raise PubErrorCustom("未找到此渠道二维码{}".format(self.xml_data))

                    aqc_obj.tot_count += 1
                    aqc_obj.follow_count += 1
                    aqc_obj.save()
                else:
                    """
                    如果用户还未关注公众号，则用户可以关注公众号，关注后微信会将带场景值关注事件推送给开发者
                    """

                    try:
                        aqc_obj = AccQrcode.objects.select_for_update().get(id=self.xml_data['EventKey'].split("qrscene_")[1])
                    except AccQrcode.DoesNotExist:
                        raise PubErrorCustom("未找到此渠道二维码{}".format(self.xml_data))

                    aqc_obj.tot_count +=1
                    aqc_obj.new_count +=1
                    aqc_obj.save()

                try:
                    alu_obj = AccLinkUser.objects.get(accid=aqc_obj.accid,openid=self.xml_data['FromUserName'])
                    alu_obj.tags = json.dumps(list(set(json.loads(alu_obj.tags)).union(set(json.loads(aqc_obj.tags)))))
                    alu_obj.save()
                except AccLinkUser.DoesNotExist:
                    alu_obj = AccLinkUser.objects.create(**{
                        "accid" : aqc_obj.accid,
                        "openid" : self.xml_data['FromUserName'],
                        "tags" : aqc_obj.tags
                    })

                #推送消息
                self.msgHandler(aqc_obj,alu_obj.openid)

            else:
                raise PubErrorCustom("事件未定义{}".format(self.xml_data))

        else:
            raise PubErrorCustom("消息类型错误!{}".format(self.xml_data['MsgType']))


    def msgHandler(self,aqc_obj,toUser):

        if aqc_obj.qr_type == '0':
            if aqc_obj.send_type == '0':
                """
                随机推送一条消息
                """
                id = random.choice(json.loads(aqc_obj.listids))
                item = AccQrcodeList.objects.filter(id=id)
                if item.type == '5':
                    self.videoSend(item, toUser)
                elif item.type == '2':
                    self.imgSend(item, toUser)
                elif item.type == '3':
                    self.textSend(item, toUser)
                elif item.type == '4':
                    self.voiceSend(item.toUser)
            else:
                """
                推送全部消息
                """
                for item in AccQrcodeList.objects.filter(id__in=json.loads(aqc_obj.listids)).order_by('sort'):
                    if item.type=='5':
                        self.videoSend(item,toUser)
                    elif item.type=='2':
                        self.imgSend(item,toUser)
                    elif item.type=='3':
                        self.textSend(item,toUser)
                    elif item.type=='4':
                        self.voiceSend(item.toUser)
                pass

    def videoSend(self,obj,toUser):

        mObj = Meterial.objects.get(media_id=obj.media_id)

        self.request_handler(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/message/mass/send?access_token={}".format(
                               self.auth_accesstoken),
                           json={
                               "touser":[
                                   toUser,
                                   ""
                               ],
                               "mpvideo":{
                                  "media_id":obj.media_id,
                                  "title":mObj.title,
                                  "description":mObj.introduction
                               },
                                "msgtype":"mpvideo"
                            })

    def imgSend(self,obj,toUser):
        self.request_handler(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/message/mass/send?access_token={}".format(
                               self.auth_accesstoken),
                           json={
                               "touser":[
                                   toUser,
                                   ""
                               ],
                               "images":{
                                    "media_ids":[
                                        obj.media_id
                                    ],
                                   "need_open_comment": 1,
                                   "only_fans_can_comment": 0
                               },
                                "msgtype":"image"
                            })

    def voiceSend(self,obj,toUser):
        self.request_handler(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/message/mass/send?access_token={}".format(
                               self.auth_accesstoken),
                           json={
                               "touser":[
                                   toUser,
                                   ""
                               ],
                               "voice": {
                                   "media_id": obj.media_id
                               },
                               "msgtype": "voice"
                            })


    def textSend(self,obj,toUser):
        self.request_handler(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/message/mass/send?access_token={}".format(
                               self.auth_accesstoken),
                           json={
                               "touser":[
                                   toUser,
                                   ""
                               ],
                               "text": {"content": obj.content},
                               "msgtype": "text"
                            })