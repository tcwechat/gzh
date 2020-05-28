
import json,random
from lib.utils.wechat.base import WechatBase
from lib.utils.wechat.WXBizMsgCrypt import WXBizMsgCrypt
from lib.utils.exceptions import PubErrorCustom
import xmltodict
from lib.utils.wechat.user import WechatAccUser,WeChatAccTag
from app.wechat.models import AccQrcode,AccLinkUser,AccQrcodeList,AccQrcodeImageTextList,AccFollow
from app.public.models import Meterial
from lib.utils.mytime import UtilTime
from lib.utils.log import logger
from lib.utils.task.follow import Follow

class WeChatAccEvent(WechatBase):

    def __init__(self,**kwargs):

        authorizer_appid = kwargs.get("authorizer_appid",None)
        # if not authorizer_appid:
        #     raise PubErrorCustom("authorizer_appid void!")

        super().__init__(isAccessToken=True,authorizer_appid=authorizer_appid)

        if kwargs.get("isDecryptMsg",None):
            res = self.DecryptMsg(
                kwargs.get("timestamp"),
                kwargs.get("nonce"),
                kwargs.get("signature"),
                kwargs.get("xmlc")
            )
            if res[0] != 0:
                raise PubErrorCustom("解密错误!{}".format(res[0]))

            self.xml_data = xmltodict.parse(res[1])['xml']

        self.rContent= None

        # self.isSend = kwargs.get("isSend",None)

    def DecryptMsg(self,timestamp,nonce,signature,xmlc):

        return WXBizMsgCrypt(self.token,self.key,self.appid).DecryptMsg(xmlc,signature,timestamp,nonce)

    def EncryptMsg(self,msg):

        return WXBizMsgCrypt(self.token,self.key,self.appid).EncryptMsg(msg)

    def linkUser(self):

        userinfo = WechatAccUser(auth_accesstoken=self.auth_accesstoken).get_info(self.xml_data['FromUserName'])

        ut = UtilTime()
        try:
            alu_obj = AccLinkUser.objects.get(accid=self.acc.accid, openid=self.xml_data['FromUserName'])
            # alu_obj.tags = json.dumps(list(set(json.loads(alu_obj.tags)).union(set(json.loads(aqc_obj.tags)))))
            alu_obj.tags = json.dumps(userinfo['tagid_list']).replace(" ", "")
            alu_obj.nickname = userinfo['nickname']
            alu_obj.sex = userinfo['sex']
            alu_obj.city = userinfo['city']
            alu_obj.province = userinfo['province']
            alu_obj.country = userinfo['country']
            alu_obj.headimgurl = userinfo['headimgurl']
            alu_obj.subscribe_time = userinfo['subscribe_time']
            alu_obj.subscribe_scene = userinfo['subscribe_scene']
            alu_obj.umark = '0'
            alu_obj.last_active_time = ut.timestamp
            alu_obj.save()

        except AccLinkUser.DoesNotExist:
            AccLinkUser.objects.create(**dict(
                accid=self.acc.accid,
                openid=self.xml_data['FromUserName'],
                tags=json.dumps(userinfo['tagid_list']).replace(" ", ""),
                nickname=userinfo['nickname'],
                sex=userinfo['sex'],
                city=userinfo['city'],
                province=userinfo['province'],
                country=userinfo['country'],
                headimgurl=userinfo['headimgurl'],
                subscribe_time=userinfo['subscribe_time'],
                subscribe_scene=userinfo['subscribe_scene'],
                last_active_time=ut.timestamp,
                umark='0'
            ))

        return userinfo

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
                        logger.info("未找到此渠道二维码{}".format(self.xml_data))
                        return "success"

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
                        logger.info("未找到此渠道二维码{}".format(self.xml_data))
                        return "success"

                    aqc_obj.tot_count +=1
                    aqc_obj.new_count +=1
                    aqc_obj.save()

                """
                先给此用户打标签
                """
                for item in json.loads(aqc_obj.tags):
                    WeChatAccTag(auth_accesstoken=self.auth_accesstoken).batchtagging([self.xml_data['FromUserName']],item)

                userinfo = self.linkUser()

                #推送消息
                if aqc_obj.qr_type == '0':
                    return self.msgHandler(
                        send_type=aqc_obj.send_type,
                        listids=aqc_obj.listids,
                        user={
                            "openid":userinfo['openid'],
                            "nickname":userinfo['nickname']
                        }
                    )
                else:
                    return "success"

            elif self.xml_data['Event'] == 'subscribe':
                if self.acc.follow_setting !='0':
                    return "success"
                else:
                    try:
                        obj = AccFollow.objects.get(accid=self.acc.accid)
                    except AccFollow.DoesNotExist:
                        logger.error("公众号{}无设置{}".format(self.acc.accid,self.xml_data))
                        return "success"

                    if obj.send_type == '0':
                        send_type = '1'
                    elif obj.send_type == '1':
                        send_type = '2'
                    elif obj.send_type == '2':
                        send_type = '0'
                    else :
                        logger.error("公众号{}推送标志有误!".format(self.acc.accid))

                    userinfo = self.linkUser()

                    return self.msgHandler(
                        send_type=send_type,
                        listids=obj.listids,
                        user={
                            "openid":userinfo['openid'],
                            "nickname":userinfo['nickname']
                        }
                    )
            elif self.xml_data['Event'] == 'CLICK':
                userinfo = self.linkUser()
            elif self.xml_data['Event'] == 'VIEW':
                userinfo = self.linkUser()
            else:
                logger.error("事件未定义{}".format(self.xml_data))
                return "success"
        elif self.xml_data['MsgType'] == 'text':
            userinfo = self.linkUser()
        elif self.xml_data['MsgType'] == 'image':
            userinfo = self.linkUser()
        elif self.xml_data['MsgType'] == 'voice':
            userinfo = self.linkUser()
        elif self.xml_data['MsgType'] == 'video':
            userinfo = self.linkUser()
        elif self.xml_data['MsgType'] == 'shortvideo':
            userinfo = self.linkUser()
        elif self.xml_data['MsgType'] == 'location':
            userinfo = self.linkUser()
        elif self.xml_data['MsgType'] == 'link':
            userinfo = self.linkUser()
        else:
            logger.error("消息类型错误!{}".format(self.xml_data['MsgType']))
            return "success"

        return "success"

    def msgHandler(self,**kwargs):

        send_type = kwargs.get("send_type",None)
        listids = kwargs.get("listids",None)
        user = kwargs.get("user",None)
        isSend = kwargs.get("isSend",None)
        sendlimit = kwargs.get("sendlimit",None)

        """
            send_type:
            0-随机推送一条
            1-全部推送
            2-按顺序推送
        """
        wamClass = WechatAccMsg(auth_accesstoken=self.auth_accesstoken)

        if send_type == '0':
            """
            随机推送一条消息
            """
            id = random.choice(json.loads(listids))
            item = AccQrcodeList.objects.filter(id=id)[0]
            if item.type == '5':
                wamClass.videoSend(item, user)
            elif item.type == '2':
                wamClass.imgSend(item, user)
            elif item.type == '3':
                wamClass.textSend(item, user)
            elif item.type == '4':
                wamClass.voiceSend(item,user)
            elif item.type == '1':
                wamClass.newsSend(item,user)
        elif send_type == '1':
            """
            推送全部消息
            """
            for j,item in enumerate(AccQrcodeList.objects.filter(id__in=json.loads(listids)).order_by('sort')):
                if item.type=='5':
                    wamClass.videoSend(item,user)
                elif item.type=='2':
                    wamClass.imgSend(item,user)
                elif item.type=='3':
                    wamClass.textSend(item,user)
                elif item.type=='4':
                    wamClass.voiceSend(item,user)
                elif item.type == '1':
                    if j==0:
                        self.rContent = self.newsHandler(item,user)
                    else:
                        wamClass.newsSend(item, user)
        elif send_type == '2':

            if isSend:
                item = AccQrcodeList.objects.filter(id=listids[0])
                if item.type == '5':
                    wamClass.videoSend(item, user)
                elif item.type == '2':
                    wamClass.imgSend(item, user)
                elif item.type == '3':
                    wamClass.textSend(item, user)
                elif item.type == '4':
                    wamClass.voiceSend(item, user)
                elif item.type == '1':
                    wamClass.newsSend(item, user)
            else:
                try:
                    Follow().sendtask(
                        {
                            "sendlimit":sendlimit,
                            "listids":listids,
                        },
                        nickname=user['nickname'],
                        openid=user['openid'],
                        accid=self.acc.accid
                    )
                except Exception as e:
                    logger.info(str(e))

        return self.rContent  if self.rContent else  "success"


    def newsHandler(self,obj,user):

        count = 0
        content=""
        for j,item in enumerate(AccQrcodeImageTextList.objects.filter(id__in=json.loads(obj.iamgetextids)).order_by('sort')):
            count+=1
            content+="<item>"
            content+="<Title><![CDATA[{}]]></Title>".format(item.title.replace("<粉丝昵称>",user['nickname']))
            content+="<Description><![CDATA[{}]]></Description>".format(item.description)
            content+="<PicUrl><![CDATA[{}]]></PicUrl>".format(item.picurl)
            content+="<Url><![CDATA[{}]]></Url>".format(item.url)
            content+="</item>"

        c = """
            <xml>
              <ToUserName><![CDATA[{}]]></ToUserName>
              <FromUserName><![CDATA[{}]]></FromUserName>
              <CreateTime>{}</CreateTime>
              <MsgType><![CDATA[news]]></MsgType>
              <ArticleCount>{}</ArticleCount>
              <Articles>
                {}
              </Articles>
            </xml>
        """.format(
            user['openid'],
            self.acc.user_name,
            UtilTime().timestamp,
            count,
            content
        )

        res = self.EncryptMsg(c)
        if res[0] != 0:
            raise PubErrorCustom("加密错误!{}".format(res[0]))
        logger.info(res)

        return res[1]

class WechatAccMsg(WechatBase):

    def __init__(self,**kwargs):

        super().__init__()
        self.url = "https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={}".format(kwargs.get("auth_accesstoken"))

    def newsSend(self,obj,user):

        articles=[]
        for item in AccQrcodeImageTextList.objects.filter(id__in=json.loads(obj.iamgetextids)).order_by('sort'):
            articles.append({
                "title":item.title.replace("<粉丝昵称>",user['nickname']),
                "description":item.description,
                "url":item.url,
                "picurl":item.picurl
            })
            break

        data = json.dumps({
                    "touser":user['openid'],
                    "msgtype":"news",
                    "news": {
                        "articles": articles
                    }
                }, ensure_ascii=False).encode('utf-8')

        if len(articles):
            self.request_handler(
                method="POST",
                url=self.url,
                data=data)

    def videoSend(self,obj,user):

        mObj = Meterial.objects.get(media_id=obj.media_id)

        self.request_handler(
            method="POST",
            url=self.url,
            json={
                "touser": user['openid'],
                "msgtype":"video",
                "video":
                {
                  "media_id":obj.media_id,
                  "title":mObj.title,
                  "description":mObj.introduction
                }
            })

    def imgSend(self,obj,user):
        self.request_handler(
            method="POST",
            url=self.url,
            json={
                "touser": user['openid'],
                "msgtype":"image",
                "image":
                {
                  "media_id":obj.media_id
                }
            })

    def voiceSend(self,obj,user):
        self.request_handler(
            method="POST",
            url=self.url,
            json={
                "touser": user['openid'],
                "msgtype":"voice",
                "voice":
                {
                  "media_id":obj.media_id
                }
            })


    def textSend(self,obj,user):

        data={
                "touser": user['openid'],
                "msgtype":"text",
                "text":
                {
                     "content":obj.content.replace("<粉丝昵称>",user['nickname'])
                }
            }
        data=json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.request_handler(
            method="POST",
            url=self.url,
            data=data)