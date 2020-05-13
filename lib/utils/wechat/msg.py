
import json
from lib.utils.wechat.base import WechatBase
from lib.utils.wechat.WXBizMsgCrypt import WXBizMsgCrypt
from lib.utils.exceptions import PubErrorCustom
import xmltodict
from app.wechat.models import AccQrcode,AccLinkUser

class WechatAccMsg(WechatBase):

    def __init__(self,**kwargs):
        super().__init__()

        res = self.DecryptMsg(
            kwargs.get("timestamp"),
            kwargs.get("nonce"),
            kwargs.get("signature"),
            kwargs.get("xmlc")
        )
        if res[0] != 0:
            raise PubErrorCustom("解密错误!{}".format(res[0]))

        self.xml_data = xmltodict.parse(res[1])

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
                    alu_obj.tags = json.loads(alu_obj.tags)
                    alu_obj.tags = json.dumps(list(set(json.loads(alu_obj.tags)).union(set(json.loads(aqc_obj.tags)))))
                    alu_obj.save()
                except AccLinkUser.DoesNotExist:
                    AccLinkUser.objects.create(**{
                        "accid" : aqc_obj.accid,
                        "openid" : self.xml_data['FromUserName'],
                        "tags" : aqc_obj.tags
                    })

            else:
                raise PubErrorCustom("事件未定义{}".format(self.xml_data))

        else:
            raise PubErrorCustom("消息类型错误!{}".format(self.xml_data['MsgType']))