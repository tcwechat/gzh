
import json,os
import xml.etree.cElementTree as ET

from rest_framework import viewsets
from lib.core.decorator.response import Core_connector
from rest_framework.decorators import list_route,detail_route
from django.shortcuts import HttpResponse

from django.db.models import Q

from project.settings import BASE_DIR

from lib.utils.wechat.ticket import WechatMsgValid
from lib.utils.wechat.msg import WeChatAccEvent
from lib.utils.wechat.base import WechatBaseForUser
from lib.utils.wechat.qrcode import WechatQrcode
from lib.utils.wechat.user import WeChatAccTag,WechatAccUser
from lib.utils.db import RedisTicketHandler

from lib.utils.mytime import UtilTime

from app.wechat.models import Acc,AccTag as AccTagModel,AccQrcode as AccQrcodeModel,AccQrcodeList,AccQrcodeImageTextList,AccLinkUser
from app.public.models import Meterial
from lib.utils.exceptions import PubErrorCustom

from lib.utils.log import logger

from app.wechat.serialiers import AccSerializer,AccTagModelSerializer,AccQrcodeModelSerializer,AccLinkUserSerializer

class WeChatAPIView(viewsets.ViewSet):

    @list_route(methods=['POST'])
    @Core_connector(isReturn=True,isRVliad=True)
    def notice(self,request, *args, **kwargs):

        """
        验证票据获取
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        xml_content = WechatMsgValid(xmltext=request.body.decode('utf-8')).run(
            request.query_params['timestamp'],
            request.query_params['nonce'],
            request.query_params['msg_signature']
        )

        # print("拆解信息:{}".format(xml_content))

        InfoType = ET.fromstring(xml_content).find("InfoType").text

        if InfoType == 'component_verify_ticket':
            RedisTicketHandler().set(ET.fromstring(xml_content).find("ComponentVerifyTicket").text)

            print("验证票据获取成功!")
        else:
            print("类型有误: {}".format(InfoType))
            raise PubErrorCustom("类型有误!")

        return HttpResponse("success")

    @list_route(methods=['POST','GET'])
    @Core_connector(isReturn=True,isTransaction=True)
    def authCallback(self,request, *args, **kwargs):

        """
        授权后回调处理
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        auth_code = request.query_params['auth_code']
        expires_in =  request.query_params['expires_in']

        t = WechatBaseForUser(isAccessToken=True)

        authorization_info = t.get_auth_by_authcode(auth_code)
        authorizer_info = t.get_authorizer_info(authorization_info)


        try:
            accObj = Acc.objects.get(authorizer_appid=authorization_info['authorizer_appid'])
            accObj.authorizer_refresh_token = authorization_info['authorizer_refresh_token']
            accObj.nick_name = authorizer_info['nick_name']
            accObj.head_img = authorizer_info['head_img']
            accObj.user_name = authorizer_info['user_name']
            accObj.service_type_info = json.dumps(authorizer_info['service_type_info'])
            accObj.verify_type_info = json.dumps(authorizer_info['verify_type_info'])
            accObj.principal_name = authorizer_info['principal_name']
            accObj.alias = authorizer_info['alias']
            accObj.qrcode_url = authorizer_info['qrcode_url']
            accObj.save()
        except Acc.DoesNotExist:
            accObj = Acc.objects.create(**dict(
                authorizer_appid = authorization_info['authorizer_appid'],
                authorizer_refresh_token = authorization_info['authorizer_refresh_token'],
                nick_name = authorizer_info['nick_name'],
                head_img = authorizer_info['head_img'],
                service_type_info=json.dumps(authorizer_info['service_type_info']),
                verify_type_info=json.dumps(authorizer_info['verify_type_info']),
                user_name=authorizer_info['user_name'],
                principal_name=authorizer_info['principal_name'],
                alias=authorizer_info['alias'],
                # business_info=json.dumps(authorizer_info['business_info']),
                qrcode_url=authorizer_info['qrcode_url'],
            ))

        t.refrech_auth_access_token(accObj.accid,authorization_info['authorizer_access_token'],authorization_info['expires_in'])

        return HttpResponse("success")

    @detail_route(methods=['POST'])
    @Core_connector(isReturn=True,isRVliad=True,isTransaction=True)
    def callback(self,request, *args, **kwargs):

        pk= kwargs.get("pk")

        res = WeChatAccEvent(
            timestamp=request.query_params['timestamp'],
            nonce=request.query_params['nonce'],
            signature=request.query_params['msg_signature'],
            xmlc=request.body.decode('utf-8'),
            authorizer_appid=pk
        ).eventHandler()

        return HttpResponse(res)


    @list_route(methods=['GET'])
    @Core_connector()
    def getPreAuthUrl(self,request):

        """
        获取授权Url
        :param request:
        :return:
        """
        return {"data":WechatBaseForUser(isAccessToken=True).get_auth_url()}

    @list_route(methods=['GET'])
    @Core_connector(isTicket=True)
    def getAcc(self,request):

        """
        获取公众号
        :param request:
        :return:
        """
        return {"data":AccSerializer(Acc.objects.filter(),many=True).data}

    @list_route(methods=['POST','GET','PUT','DELETE'])
    @Core_connector(isTransaction=True,isPagination=True)
    def AccTag(self,request,*args,**kwargs):

        if request.method =='POST':

            id = WeChatAccTag(accid=request.data_format.get("accid")).create(request.data_format.get("name"))

            obj = AccTagModel.objects.create(**dict(
                id = id,
                name = request.data_format.get("name"),
                accid = request.data_format.get("accid")
            ))
            return {"data":{"id":obj.id}}

        elif request.method =='PUT':
            try:
                obj = AccTagModel.objects.get(id=request.data_format.get("id"))
                obj.name = request.data_format.get("name")

                WeChatAccTag(accid=request.data_format.get("accid")).update(obj.id,obj.name)

                obj.save()
            except AccTagModel.DoesNotExist:
                raise PubErrorCustom("不存在此标签!")

        elif request.method == 'DELETE':
            try:
                obj = AccTagModel.objects.get(id=request.data_format.get("id"))
                WeChatAccTag(accid=request.data_format.get("accid")).delete(id=obj.id)
                obj.delete()
            except AccTagModel.DoesNotExist:
                raise PubErrorCustom("不存在此标签!")

        elif request.method == 'GET':
            query = AccTagModel.objects.filter(accid=request.query_params_format.get("accid"),umark='0')
            count = query.count()
            return { "data":AccTagModelSerializer(query[request.page_start:request.page_end],many=True).data,"count":count }

        else:
            raise PubErrorCustom("拒绝访问!")

        return None

    @list_route(methods=['POST'])
    @Core_connector()
    def AccTag_sync(self, request):
        """
        同步标签
        :param request:
        :return:
        """

        runprogram = os.path.join(BASE_DIR,'run')

        run="nohup python {}/tag_sync.py {} 1>>{}/logs/tag_sync.log 2>&1 &".format(runprogram,request.data_format.get("accid",0),BASE_DIR)
        logger.info(run)
        os.system(run)

        return None

    @list_route(methods=['GET'])
    @Core_connector(isPagination=True)
    def AccUser_get(self, request):

        query = AccLinkUser.objects.filter(accid=request.query_params_format.get("accid",None),umark='0')

        nickname = request.query_params_format.get("nickname",None)
        sex = request.query_params_format.get("sex",None)
        subscribe_start = request.query_params_format.get("subscribe_start",None)
        subscribe_end = request.query_params_format.get("subscribe_end", None)
        subscribe_scene = request.query_params_format.get("subscribe_scene", None)
        province = request.query_params_format.get("province", None)
        city = request.query_params_format.get("city", None)
        tagid1 = request.query_params_format.get("tagid1",None)

        if nickname:
            query = query.filter(Q(nickname=nickname) | Q(memo=nickname))
        if sex:
            query = query.filter(sex=sex)
        if subscribe_scene:
            query = query.filter(subscribe_scene=subscribe_scene)
        if province:
            query = query.filter(province=province)
        if city:
            query = query.filter(city=city)
        if tagid1:
            query = query.filter(Q(tags__icontains=",{}".format(tagid1)) | Q(tags__icontains="{},".format(tagid1)))

        if subscribe_start:
            ut = UtilTime()
            if not subscribe_end:
                subscribe_end = ut.arrow_to_timestamp()
            subscribe_start = ut.string_to_timestamp(subscribe_start)

            query = query.filter(subscribe_time__gte=subscribe_start,subscribe_time__lte=subscribe_end)

        query.order_by('-subscribe_time')
        count = query.count()

        return {"data":AccLinkUserSerializer(query[request.page_start:request.page_end],many=True).data,"count":count}

    @list_route(methods=['POST'])
    @Core_connector()
    def AccUser_sync(self, request):
        """
        同步粉丝
        :param request:
        :return:
        """

        runprogram = os.path.join(BASE_DIR,'run')

        run="nohup python {}/user_sync.py {} 1>>{}/logs/user_sync.log 2>&1 &".format(runprogram,request.data_format.get("accid",0),BASE_DIR)
        logger.info(run)
        os.system(run)

        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccUser_batchtagging(self, request):
        """
        一键标签
        :param request:
        :return:
        """
        query = AccLinkUser.objects.filter(accid=request.data_format.get("accid", None), umark='0')

        nickname = request.data_format.get("nickname", None)
        sex = request.data_format.get("sex", None)
        subscribe_start = request.data_format.get("subscribe_start", None)
        subscribe_end = request.data_format.get("subscribe_end", None)
        subscribe_scene = request.data_format.get("subscribe_scene", None)
        province = request.data_format.get("province", None)
        city = request.data_format.get("city", None)

        tagid = request.data_format.get("tagid", None)
        tagid1 = request.query_params_format.get("tagid1",None)

        if not tagid:
            raise PubErrorCustom("tagid为空!")

        if nickname:
            query = query.filter(Q(nickname=nickname) | Q(memo=nickname))
        if sex:
            query = query.filter(sex=sex)
        if subscribe_scene:
            query = query.filter(subscribe_scene=subscribe_scene)
        if province:
            query = query.filter(province=province)
        if city:
            query = query.filter(city=city)
        if tagid1:
            query = query.filter(Q(tags__icontains=",{}".format(tagid1)) | Q(tags__icontains="{},".format(tagid1)))

        if subscribe_start:
            ut = UtilTime()
            if not subscribe_end:
                subscribe_end = ut.arrow_to_timestamp()
            subscribe_start = ut.string_to_timestamp(subscribe_start, format_v="YYYY-MM-DD HH:mm")

            query = query.filter(subscribe_time__gte=subscribe_start, subscribe_time__lte=subscribe_end)

        openids=[]
        valid_count = 0
        for item in query:
            tags = json.loads(item.tags)
            if int(tagid) not in tags:
                tags.append(tagid)
                item.tags=json.dumps(tags).replace(" ","")
                item.save()
                valid_count += 1
            openids.append(item.openid)

        if valid_count:
            try:
                atmObj = AccTagModel.objects.select_for_update().get(id=tagid)
                atmObj.fans_count += valid_count
                atmObj.wechat_fans_count += valid_count
                atmObj.save()
            except AccTagModel.DoesNotExist:
                raise PubErrorCustom("无此标签!")

        if len(openids):
            WeChatAccTag(accid=request.data_format.get("accid", None)).batchtagging(openids,int(tagid))

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccUser_batchtagging1(self, request):
        """
        打标签
        :param request:
        :return:
        """

        tagid = request.data_format.get("tagid", None)
        openids = request.data_format.get("openids", [])

        query = AccLinkUser.objects.filter(accid=request.data_format.get("accid", None), umark='0',openid__in=openids)

        openids=[]
        valid_count = 0
        for item in query:
            tags = json.loads(item.tags)
            if int(tagid) not in tags:
                tags.append(tagid)
                item.tags=json.dumps(tags).replace(" ","")
                item.save()
                valid_count+=1
            openids.append(item.openid)

        if valid_count:
            try:
                atmObj = AccTagModel.objects.select_for_update().get(id=tagid)
                atmObj.fans_count += valid_count
                atmObj.wechat_fans_count += valid_count
                atmObj.save()
            except AccTagModel.DoesNotExist:
                raise PubErrorCustom("无此标签!")

        if len(openids):
            WeChatAccTag(accid=request.data_format.get("accid", None)).batchtagging(openids, int(tagid))

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccUser_upd(self, request):
        try:
            obj = AccLinkUser.objects.get(accid=request.data_format.get("accid", None), umark='0',openid=request.data_format.get("openid", None))
            obj.memo = request.data_format.get("memo", "")
            obj.save()
        except AccLinkUser.DoesNotExist:
            raise PubErrorCustom("无此用户!")

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccQrcode(self,request,*args,**kwargs):

        obj = AccQrcodeModel.objects.create(**dict(
            name=request.data_format.get('name'),
            accid=request.data_format.get('accid'),
            type=request.data_format.get('type'),
            qr_type=request.data_format.get('qr_type'),
            send_type=request.data_format.get('send_type'),
            tags=json.dumps(request.data_format.get('tags')),
        ))
        obj.listids = json.loads(obj.listids)

        wQClass= WechatQrcode(accid=obj.accid)
        # waUClass = WechatAccUser(auth_accesstoken=wQClass.auth_accesstoken).get_info()

        for c,item in enumerate(request.data_format.get('lists')):
            aqlObj = AccQrcodeList.objects.create(**dict(
                type=item.get("type"),
                qrid=obj.id,
                media_id=item.get("media_id", ""),
                content=item.get("content", ""),
                sort=c+1
            ))
            obj.listids.append(aqlObj.id)

            if str(item.get("type")) == '1':

                # articles = []

                aqlObj.iamgetextids = json.loads(aqlObj.iamgetextids)

                for j,cItem in enumerate(item.get("imagetextlist")):

                    try:
                        mObj = Meterial.objects.get(media_id=cItem.get("media_id", ""))
                    except Meterial.DoesNotExist:
                        raise PubErrorCustom("无此媒体数据{}".format(cItem.get("media_id", "")))

                    aqitlObj = AccQrcodeImageTextList.objects.create(**dict(
                        qr_listid=aqlObj.id,
                        picurl=mObj.url,
                        media_id=mObj.media_id,
                        url=cItem.get("url", ""),
                        title=cItem.get("title", ""),
                        description=cItem.get("description", ""),
                        sort=j+1
                    ))
                    aqlObj.iamgetextids.append(aqitlObj.id)

                    # articles.append(dict(
                    #     title = aqitlObj.title,
                    #     thumb_media_id = aqitlObj.media_id,
                    #     show_cover_pic = "1",
                    #     content=aqitlObj.description,
                    #     content_source_url=aqitlObj.url
                    # ))
                # media_id = wQClass.image_text_create(articles)

                aqlObj.iamgetextids = json.dumps(aqlObj.iamgetextids)
                aqlObj.save()

        obj.listids = json.dumps(obj.listids)

        if obj.type == '0':
            obj.url = wQClass.qrcode_create(obj.id)
        else:
            obj.url = wQClass.qrcode_create_forever(obj.id)

        obj.save()

        return None

    @list_route(methods=['GET'])
    @Core_connector(isPagination=True)
    def AccQrcode_get(self, request, *args, **kwargs):


        query = AccQrcodeModel.objects.filter(accid=request.query_params_format.get("accid",0))

        if request.query_params_format.get("name",None):
            query= query.filter(name__contains=request.query_params_format.get("name",None))


        query = query.order_by('-createtime')

        count = query.count()

        return {"data":AccQrcodeModelSerializer(query[request.page_start:request.page_end],many=True).data,"count":count}


    @list_route(methods=['PUT'])
    @Core_connector(isTransaction=True)
    def AccQrcode_upd(self,request,*args,**kwargs):

        try:
            obj = AccQrcodeModel.objects.get(id=request.data_format.get("id"))
        except AccQrcodeModel.DoesNotExist:
            raise PubErrorCustom("无此二维码!")


        type = obj.type

        obj.name = request.data_format.get('name')
        obj.accid = request.data_format.get('accid')
        obj.type = request.data_format.get('type')
        obj.qr_type = request.data_format.get('qr_type')
        obj.send_type = request.data_format.get('send_type')
        obj.tags = json.dumps(request.data_format.get('tags'))
        obj.listids = []

        for c,item in enumerate(request.data_format.get('lists')):
            if item.get("id",None):
                try:
                    aqlObj = AccQrcodeList.objects.get(id=item.get("id",None))
                except AccQrcodeList.DoesNotExist:
                    raise PubErrorCustom("无此内容明细!")
                aqlObj.type = item.get("type")
                aqlObj.qrid=obj.id
                aqlObj.media_id=item.get("media_id", "")
                aqlObj.content = item.get("content", "")
                aqlObj.sort = c+1
            else:
                aqlObj = AccQrcodeList.objects.create(**dict(
                    type=item.get("type"),
                    qrid=obj.id,
                    media_id=item.get("media_id", ""),
                    content=item.get("content", ""),
                    sort = c+1
                ))

            obj.listids.append(aqlObj.id)

            if item.get("type") == '1':
                aqlObj.iamgetextids = []
                for j,cItem in enumerate(item.get("imagetextlist")):

                    try:
                        mObj = Meterial.objects.get(media_id=cItem.get("media_id", ""))
                    except Meterial.DoesNotExist:
                        raise PubErrorCustom("无此媒体数据{}".format(cItem.get("media_id", "")))

                    if cItem.get("id",None):
                        try:
                            aqitlObj = AccQrcodeImageTextList.objects.get(id=cItem.get("id",None))
                        except AccQrcodeImageTextList.DoesNotExist:
                            raise PubErrorCustom("无此图文明细!")

                        aqitlObj.qr_listid = aqlObj.id
                        aqitlObj.picurl = mObj.url
                        aqitlObj.media_id = mObj.media_id
                        aqitlObj.url = cItem.get("url", "")
                        aqitlObj.title = cItem.get("title", "")
                        aqitlObj.description = cItem.get("description", "")
                        aqitlObj.sort = j + 1
                        aqitlObj.save()
                    else:
                        aqitlObj = AccQrcodeImageTextList.objects.create(**dict(
                            qr_listid=aqlObj.id,
                            picurl=mObj.url,
                            media_id=mObj.media_id,
                            url=cItem.get("url", ""),
                            title=cItem.get("title", ""),
                            description=cItem.get("description", ""),
                            sort = j+1
                        ))
                    aqlObj.iamgetextids.append(aqitlObj.id)
                aqlObj.iamgetextids = json.dumps(aqlObj.iamgetextids)

            aqlObj.save()

        obj.listids = json.dumps(obj.listids)

        if type != request.data_format.get('type'):
            if obj.type == '0':
                obj.url = WechatQrcode(accid=obj.accid).qrcode_create(obj.id)
            else:
                obj.url = WechatQrcode(accid=obj.accid).qrcode_create_forever(obj.id)

        obj.save()

        return None


    @list_route(methods=['POST'])
    @Core_connector(isReturn=True)
    def test(self,request, *args, **kwargs):

        return HttpResponse("success")


    # @list_route(methods=['GET'])
    # @Core_connector(isReturn=True)
    # def initCheck(self,request, *args, **kwargs):
    #     print(request.query_params_format)
    #     signature = request.query_params_format.get("signature",None)
    #     timestamp = request.query_params_format.get("timestamp",None)
    #     nonce = request.query_params_format.get("nonce",None)
    #     echostr = request.query_params_format.get("echostr",None)
    #
    #
    #     token="b3aa7790500908e9a9e454b4fd1d126f"
    #     encrypt="b3aa7790500908e9a9e454b4fd1d126f"
    #
    #     if CustomHash(token=token).tokenCheck(nonce=nonce,timestamp=timestamp,signature=signature):
    #         return HttpResponse(echostr)
    #     else:
    #         return HttpResponse("")
