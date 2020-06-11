
import json,os
import xml.etree.cElementTree as ET

from rest_framework import viewsets
from lib.core.decorator.response import Core_connector
from rest_framework.decorators import list_route,detail_route
from django.shortcuts import HttpResponse

from django.db.models import Q
from django.shortcuts import render
from project.settings import BASE_DIR,ServerUrl

from lib.utils.wechat.ticket import WechatMsgValid
from lib.utils.wechat.msg import WeChatAccEvent
from lib.utils.wechat.base import WechatBaseForUser
from lib.utils.wechat.qrcode import WechatQrcode
from lib.utils.wechat.user import WeChatAccTag,WechatAccUser
from lib.utils.wechat.mouldmsg import MouldMsg
from lib.utils.db import RedisTicketHandler

from app.wechat.utils import tag_batchtagging,customMsgListAdd,customMsgListUpd

from lib.utils.mytime import UtilTime

from app.wechat.models import Acc,AccTag as AccTagModel,AccQrcode as AccQrcodeModel,AccQrcodeList,AccQrcodeImageTextList,AccLinkUser,\
                                    AccFollow,AccReply,AccSend,AccMsgCustomer,AccMsgCustomerLinkAcc,AccMsgMould,AccMsgMass
from app.public.models import Meterial
from lib.utils.exceptions import PubErrorCustom
from lib.utils.task.follow import Follow
from lib.utils.task.reply import Reply
from lib.utils.task.msgcustomer import MsgCustomer
from lib.utils.task.msgmould import MsgMould
from lib.utils.task.msgmass import MsgMass
from lib.utils.wechat.material import WechatMaterial

from lib.utils.log import logger

from app.wechat.serialiers import AccSerializer,AccTagModelSerializer,AccQrcodeModelSerializer,AccLinkUserSerializer,\
    AccFollowModelSerializer,AccReplyModelSerializer,AccSendSerializer1,AccMsgCustomerModelSerializer,AccFollowSerializer,\
        AccReplySerializer,AccMsgMouldSerializer,AccMsgMouldModelSerializer,AccMsgMassSerializer,AccQrcodeListModelSerializer1,\
            AccMsgMassModelSerializer,AccMsgCustomerModelSerializer1,AccMsgMouldModelSerializer1,AccMsgMassModelSerializer1

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

        return render(request, 'goindex.html', {
            'data': {
                "url": ServerUrl
            }
        })

    @detail_route(methods=['POST'])
    @Core_connector(isReturn=True,isRVliad=True,isTransaction=True)
    def callback(self,request, *args, **kwargs):

        pk= kwargs.get("pk")

        res = WeChatAccEvent(
            timestamp=request.query_params['timestamp'],
            nonce=request.query_params['nonce'],
            signature=request.query_params['msg_signature'],
            xmlc=request.body.decode('utf-8'),
            authorizer_appid=pk,
            isDecryptMsg=True
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
    @Core_connector(isTicket=True,isPagination=True)
    def getAcc(self,request):

        """
        获取公众号
        :param request:
        :return:
        """
        query = Acc.objects.filter()
        count = query.count()
        return {"data":AccSerializer(query[request.page_start: request.page_end],many=True).data,"count":count}

    @list_route(methods=['POST'])
    @Core_connector(isTicket=True)
    def Acc_delete(self,request):

        Acc.objects.filter(accid=request.data_format.get("accid",None)).delete()

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

        query = query.order_by('-subscribe_time')
        count = query.count()
        logger.info(count,query.count())
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

        tag_batchtagging(accid=request.data_format.get("accid", None), query=query, tagid=int(tagid))

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

        if not tagid:
            raise PubErrorCustom("tagid is void!")

        query = AccLinkUser.objects.filter(accid=request.data_format.get("accid", None), umark='0',openid__in=openids)

        tag_batchtagging(accid=request.data_format.get("accid", None),query=query,tagid=int(tagid))

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

        customMsgListAdd(obj, request.data_format.get('lists'))

        # for c,item in enumerate(request.data_format.get('lists')):
        #     aqlObj = AccQrcodeList.objects.create(**dict(
        #         type=item.get("type"),
        #         qrid=obj.id,
        #         media_id=item.get("media_id", ""),
        #         content=item.get("content", ""),
        #         sort=c+1
        #     ))
        #     obj.listids.append(aqlObj.id)
        #
        #     if str(item.get("type")) == '1':
        #
        #         # articles = []
        #
        #         aqlObj.iamgetextids = json.loads(aqlObj.iamgetextids)
        #
        #         for j,cItem in enumerate(item.get("imagetextlist")):
        #
        #             try:
        #                 mObj = Meterial.objects.get(media_id=cItem.get("media_id", ""))
        #             except Meterial.DoesNotExist:
        #                 raise PubErrorCustom("无此媒体数据{}".format(cItem.get("media_id", "")))
        #
        #             aqitlObj = AccQrcodeImageTextList.objects.create(**dict(
        #                 qr_listid=aqlObj.id,
        #                 picurl=mObj.url,
        #                 media_id=mObj.media_id,
        #                 url=cItem.get("url", ""),
        #                 title=cItem.get("title", ""),
        #                 description=cItem.get("description", ""),
        #                 sort=j+1
        #             ))
        #             aqlObj.iamgetextids.append(aqitlObj.id)
        #
        #             # articles.append(dict(
        #             #     title = aqitlObj.title,
        #             #     thumb_media_id = aqitlObj.media_id,
        #             #     show_cover_pic = "1",
        #             #     content=aqitlObj.description,
        #             #     content_source_url=aqitlObj.url
        #             # ))
        #         # media_id = wQClass.image_text_create(articles)
        #
        #         aqlObj.iamgetextids = json.dumps(aqlObj.iamgetextids)
        #         aqlObj.save()

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

        customMsgListUpd(obj, request.data_format.get('lists'))

        # for c,item in enumerate(request.data_format.get('lists')):
        #     if item.get("id",None):
        #         try:
        #             aqlObj = AccQrcodeList.objects.get(id=item.get("id",None))
        #         except AccQrcodeList.DoesNotExist:
        #             raise PubErrorCustom("无此内容明细!")
        #         aqlObj.type = item.get("type")
        #         aqlObj.qrid=obj.id
        #         aqlObj.media_id=item.get("media_id", "")
        #         aqlObj.content = item.get("content", "")
        #         aqlObj.sort = c+1
        #     else:
        #         aqlObj = AccQrcodeList.objects.create(**dict(
        #             type=item.get("type"),
        #             qrid=obj.id,
        #             media_id=item.get("media_id", ""),
        #             content=item.get("content", ""),
        #             sort = c+1
        #         ))
        #
        #     obj.listids.append(aqlObj.id)
        #
        #     if item.get("type") == '1':
        #         aqlObj.iamgetextids = []
        #         for j,cItem in enumerate(item.get("imagetextlist")):
        #
        #             try:
        #                 mObj = Meterial.objects.get(media_id=cItem.get("media_id", ""))
        #             except Meterial.DoesNotExist:
        #                 raise PubErrorCustom("无此媒体数据{}".format(cItem.get("media_id", "")))
        #
        #             if cItem.get("id",None):
        #                 try:
        #                     aqitlObj = AccQrcodeImageTextList.objects.get(id=cItem.get("id",None))
        #                 except AccQrcodeImageTextList.DoesNotExist:
        #                     raise PubErrorCustom("无此图文明细!")
        #
        #                 aqitlObj.qr_listid = aqlObj.id
        #                 aqitlObj.picurl = mObj.url
        #                 aqitlObj.media_id = mObj.media_id
        #                 aqitlObj.url = cItem.get("url", "")
        #                 aqitlObj.title = cItem.get("title", "")
        #                 aqitlObj.description = cItem.get("description", "")
        #                 aqitlObj.sort = j + 1
        #                 aqitlObj.save()
        #             else:
        #                 aqitlObj = AccQrcodeImageTextList.objects.create(**dict(
        #                     qr_listid=aqlObj.id,
        #                     picurl=mObj.url,
        #                     media_id=mObj.media_id,
        #                     url=cItem.get("url", ""),
        #                     title=cItem.get("title", ""),
        #                     description=cItem.get("description", ""),
        #                     sort = j+1
        #                 ))
        #             aqlObj.iamgetextids.append(aqitlObj.id)
        #         aqlObj.iamgetextids = json.dumps(aqlObj.iamgetextids)
        #
        #     aqlObj.save()

        obj.listids = json.dumps(obj.listids)

        if type != request.data_format.get('type'):
            if obj.type == '0':
                obj.url = WechatQrcode(accid=obj.accid).qrcode_create(obj.id)
            else:
                obj.url = WechatQrcode(accid=obj.accid).qrcode_create_forever(obj.id)

        obj.save()

        return None

    @list_route(methods=['PUT'])
    @Core_connector(isTransaction=True)
    def AccFollow_upd(self,request):

        try:
            obj = AccFollow.objects.get(accid=request.data_format.get("accid"))
            obj.accid = request.data_format.get('accid')
            obj.send_type = request.data_format.get('send_type')
            obj.send_limit = request.data_format.get('send_limit')
            obj.listids = []
        except AccFollow.DoesNotExist:
            obj = AccFollow.objects.create(**dict(
                accid=request.data_format.get('accid'),
                send_type=request.data_format.get('send_type'),
                send_limit=request.data_format.get('send_limit'),
            ))
            obj.listids = []

        customMsgListUpd(obj,request.data_format.get('lists'))

        obj.listids = json.dumps(obj.listids)
        obj.save()

        return None

    @list_route(methods=['DELETE'])
    @Core_connector(isTransaction=True)
    def AccFollow_del(self,request):
        AccFollow.objects.filter(accid=request.data_format.get("accid")).delete()
        return None

    @list_route(methods=['GET'])
    @Core_connector()
    def AccFollow_get(self, request, *args, **kwargs):
        try:
            query = AccFollow.objects.get(accid=request.query_params_format.get("accid",0))
            return {"data":AccFollowModelSerializer(query,many=False).data}
        except AccFollow.DoesNotExist:
            return None

    @list_route(methods=['GET'])
    @Core_connector(isPagination=True)
    def AccFollowList_get(self, request, *args, **kwargs):

        query = Acc.objects.raw("""
            SELECT t1.*,t2.send_type,t2.listids FROM acc as t1
            LEFT JOIN accfollow as t2 ON t1.accid = t2.accid
            WHERE 1=1 ORDER BY t1.createtime DESC
        """)

        count = len(list(query))

        return {"data":AccFollowSerializer(query[request.page_start:request.page_end],many=True).data,"count":count}

    @list_route(methods=['PUT'])
    @Core_connector(isTransaction=True)
    def AccFollow_flag_setting(self, request, *args, **kwargs):
        Acc.objects.filter(accid=request.data_format.get("accid")).update(follow_setting=request.data_format.get("follow_setting"))
        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccFollow_Send(self, request, *args, **kwargs):

        Follow().sendmsg(
            listid = request.data_format.get("listid",0),
            nickname = request.data_format.get("nickname",""),
            openid = request.data_format.get("openid",""),
            accid = request.data_format.get("accid",0)
        )
        return None

    @list_route(methods=['PUT'])
    @Core_connector(isTransaction=True)
    def AccReply_upd(self,request):

        trigger = request.data_format.get("trigger",[])
        if not trigger or not len(trigger):
            raise PubErrorCustom("trigger is void!")

        t = ""
        for item in trigger:
            t+=str(item)
        try:
            obj = AccReply.objects.get(accid=request.data_format.get("accid"))
            obj.accid = request.data_format.get('accid')
            obj.nosend_limit = request.data_format.get("nosend_limit")
            obj.trigger = t
            obj.quiet = "{}-{}".format(request.data_format.get("quiet")[0],request.data_format.get("quiet")[1])
            obj.send_place = request.data_format.get("send_place")
            obj.send_type = request.data_format.get('send_type')
            obj.send_limit = request.data_format.get('send_limit')
            obj.listids = []
        except AccReply.DoesNotExist:
            obj = AccReply.objects.create(**dict(
                accid=request.data_format.get('accid'),
                nosend_limit=request.data_format.get("nosend_limit"),
                trigger=t,
                quiet="{}-{}".format(request.data_format.get("quiet")[0],request.data_format.get("quiet")[1]),
                send_place=request.data_format.get("send_place"),
                send_type=request.data_format.get('send_type'),
                send_limit=request.data_format.get('send_limit'),
            ))
            obj.listids = []

        customMsgListUpd(obj,request.data_format.get('lists'))

        obj.listids = json.dumps(obj.listids)
        obj.save()

        return None

    @list_route(methods=['DELETE'])
    @Core_connector(isTransaction=True)
    def AccReply_del(self,request):
        AccReply.objects.filter(accid=request.data_format.get("accid")).delete()
        return None

    @list_route(methods=['PUT'])
    @Core_connector(isTransaction=True)
    def AccReply_flag_setting(self, request, *args, **kwargs):
        Acc.objects.filter(accid=request.data_format.get("accid")).update(reply_setting=request.data_format.get("reply_setting"))
        return None

    @list_route(methods=['GET'])
    @Core_connector()
    def AccReply_get(self, request, *args, **kwargs):

        try:
            query = AccReply.objects.get(accid=request.query_params_format.get("accid",0))
            return {"data":AccReplyModelSerializer(query,many=False).data}
        except AccReply.DoesNotExist:
            return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccReply_Send(self, request, *args, **kwargs):

        # ut = UtilTime()
        obj = request.data_format.get("obj",{})

        try:
            alObj = AccLinkUser.objects.get(accid=request.data_format.get("accid",0),openid=request.data_format.get("openid",""))
        except AccLinkUser.DoesNotExist:
            raise PubErrorCustom("无此用户!{}".format(obj))

        if alObj.last_active_time > request.data_format.get("createtime",0):
            raise PubErrorCustom("已互动,不推送消息!{}".format(obj))

        ut = UtilTime()

        start = ut.string_to_timestamp(ut.arrow_to_string(format_v="YYYY-MM-DD")+' 00:00:01')
        end = ut.string_to_timestamp(ut.arrow_to_string(format_v="YYYY-MM-DD") + ' 23:59:59')
        # today = ut.string_to_timestamp(ut.arrow_to_string(format_v="YYYY-MM-DD"),format_v="YYYY-MM-DD")

        ok_count = AccSend.objects.filter(
                createtime__gte=start,
                createtime__lte=end,
                send_type='2',accid=alObj.accid,openid=alObj.openid).count()
        logger.info(start)
        logger.info(end)
        logger.info(ok_count)
        logger.info(obj['send_place'])
        if ok_count >= obj['send_place']:
            raise PubErrorCustom("推送条数超限!{}".format(obj))

        AccSend.objects.create(**dict(
            accid=alObj.accid,
            send_type="2",
            cid=obj['id'],
            openid=alObj.openid
        ))

        Reply().sendmsg(
            count=obj['send_place'] - ok_count,
            listids = request.data_format.get("listids",0),
            send_type=request.data_format.get("send_type",""),
            nickname = request.data_format.get("nickname",""),
            openid = request.data_format.get("openid",""),
            accid = request.data_format.get("accid",0)
        )
        return None

    @list_route(methods=['GET'])
    @Core_connector(isPagination=True)
    def AccReplyList1_get(self, request, *args, **kwargs):

        query_format=str()
        query_params=list()

        if request.query_params_format.get("nick_name"):
            query_format = query_format + " and t2.nick_name =%s"
            query_params.append(request.query_params_format.get("nick_name"))

        if request.query_params_format.get("start") and request.query_params_format.get("end"):
            query_format = query_format + " and t1.date >=%s and t1.date<=%s"
            query_params.append(request.query_params_format.get("start"))
            query_params.append(request.query_params_format.get("end"))

        query = AccSend.objects.raw("""
            SELECT '1' as id,t1.date,t2.nick_name,count(*) as send_count,count(distinct(t1.openid)) as reply_count FROM accsend as t1 
                INNER JOIN acc as t2 ON t1.accid=t2.accid and t1.send_type='2'
                WHERE 1=1 %s GROUP BY t1.date,t2.nick_name ORDER BY t1.date DESC
        """% (query_format), query_params)

        count = len(list(query))

        return {"data": AccSendSerializer1(query[request.page_start:request.page_end], many=True).data, "count": count}

    @list_route(methods=['GET'])
    @Core_connector(isPagination=True)
    def AccReplyList_get(self, request, *args, **kwargs):

        query = Acc.objects.raw("""
            SELECT t1.*,t2.send_type,t2.listids,t2.nosend_limit FROM acc as t1
            LEFT JOIN accreply as t2 ON t1.accid = t2.accid
            WHERE 1=1 ORDER BY t1.createtime DESC
        """)

        count = len(list(query))

        return {"data":AccReplySerializer(query[request.page_start:request.page_end],many=True).data,"count":count}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccMsgCustomer_add(self,request,*args,**kwargs):

        obj = AccMsgCustomer.objects.create(**dict(
            name=request.data_format.get('name'),
            accids=json.dumps(request.data_format.get("accids",[])),
            sendtime=request.data_format.get('sendtime'),
            type=request.data_format.get('type'),
            select_sex=request.data_format.get("select_sex",""),
            select_followtime=request.data_format.get("select_followtime",""),
            select_province=request.data_format.get("select_province", ""),
            select_city=request.data_format.get("select_city", ""),
            select_tags=json.dumps(request.data_format.get("select_tags", [])).replace(' ',''),
        ))
        for item in request.data_format.get("accids"):
            AccMsgCustomerLinkAcc.objects.create(**dict(
                msgid=obj.id,
                accid=item
            ))

        obj.listids = json.loads(obj.listids)

        customMsgListAdd(obj,request.data_format.get('lists'))

        obj.listids = json.dumps(obj.listids)

        obj.save()

        MsgCustomer().sendtask_add(obj=AccMsgCustomerModelSerializer1(obj,many=False).data)

        return None

    @list_route(methods=['PUT'])
    @Core_connector(isTransaction=True)
    def AcMsgCustomer_upd(self,request):

        try:
            obj = AccMsgCustomer.objects.get(id=request.data_format.get("id"))
        except AccMsgCustomer.DoesNotExist:
            raise PubErrorCustom("无此信息!")

        AccMsgCustomerLinkAcc.objects.filter(msgid=obj.id).delete()

        obj.name = request.data_format.get('name')
        obj.accids = json.dumps(request.data_format.get("accids", []))
        obj.sendtime = request.data_format.get('sendtime')
        obj.type = request.data_format.get('type')
        obj.select_sex = request.data_format.get("select_sex", "")
        obj.select_followtime = request.data_format.get("select_followtime", "")
        obj.select_province = request.data_format.get("select_province", "")
        obj.select_city = request.data_format.get("select_city", "")
        obj.select_tags = json.dumps(request.data_format.get("select_tags", [])).replace(' ','')

        for item in request.data_format.get("accids"):
            AccMsgCustomerLinkAcc.objects.create(**dict(
                msgid=obj.id,
                accid=item
            ))

        customMsgListUpd(obj,request.data_format.get('lists'))

        obj.listids = json.dumps(obj.listids)
        obj.save()

        MsgCustomer().sendtask_upd(obj=AccMsgCustomerModelSerializer1(obj,many=False).data)

        return None

    @list_route(methods=['DELETE'])
    @Core_connector(isTransaction=True)
    def AcMsgCustomer_del(self,request):
        AccMsgCustomer.objects.filter(id=request.data_format.get("id")).delete()
        AccMsgCustomerLinkAcc.objects.filter(msgid=request.data_format.get("id")).delete()

        MsgCustomer().sendtask_del(request.data_format.get("id"))
        return None


    @list_route(methods=['GET'])
    @Core_connector(isPagination=True)
    def AccMsgCustomer_get(self, request, *args, **kwargs):

        ut = UtilTime()

        query = AccMsgCustomer.objects.filter()

        start = request.query_params_format.get("star",None)
        end = request.query_params_format.get("end",ut.timestamp)

        status = request.query_params_format.get("status",None)

        if start:
            query = query.filter(sendtime__gte=start,senditme__lte=end)

        if status:
            query = query.filter(status=status)

        count = query.count()

        return {"data": AccMsgCustomerModelSerializer(query[request.page_start:request.page_end], many=True).data, "count": count}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccMsgCustomer_Send(self, request, *args, **kwargs):

        try:
            obj = AccMsgCustomer.objects.get(id=request.data_format.get("id"))
        except AccMsgCustomer.DoesNotExist:
            raise PubErrorCustom("无此信息!")

        isOk=True
        for amclaItem in AccMsgCustomerLinkAcc.objects.filter(msgid=obj.id):
            query_format=str()
            query_params=list()

            query_format = query_format + " and t1.accid =%s"
            query_params.append(str(amclaItem.accid))

            if obj.type != '1':
                if obj.select_sex in ['0','1','2']:
                    query_format = query_format + " and t1.sex =%s"
                    query_params.append(obj.select_sex)
                if len(obj.select_followtime):
                    start = obj.select_followtime.split('-')[0]
                    end = obj.select_followtime.split('-')[1]
                    query_format = query_format + " and t1.subscribe_time>=%s and t1.subscribe_time<=%s"
                    query_params.append(start)
                    query_params.append(end)
                if len(obj.select_province):
                    query_format = query_format + " and t1.province=%s"
                    query_params.append(obj.select_province)
                if len(obj.select_city):
                    query_format = query_format + " and t1.city=%s"
                    query_params.append(obj.select_city)

                select_tags = json.loads(obj.select_tags)
                if len(select_tags):
                    query_format = query_format + " and ("
                    for j,item in enumerate(select_tags):
                        if j>0:
                            query_format = query_format + " or "

                        query_format = query_format + " (t1.tags like %s or t1.tags like %s)"
                        query_params.append("%,{}%".format(item))
                        query_params.append("%{},%".format(item))


                    query_format = query_format + " )"


            res = AccLinkUser.objects.raw("""
                SELECT t1.* FROM acclinkuser as t1
                WHERE t1.umark='0' %s
            """% (query_format), query_params)

            logger.info(res)
            amclaItem.send_count1 = len(list(res))
            obj.send_count1 += amclaItem.send_count1

            for aluItem in res:
                try:
                    MsgCustomer().sendmsg(
                        listids=obj.listids,
                        nickname=aluItem.nickname,
                        openid=aluItem.openid,
                        accid=aluItem.accid
                    )
                    amclaItem.send_count+=1
                    obj.send_count+=1
                except Exception as e:
                    logger.error(str(e))

            if amclaItem.send_count ==0:
                amclaItem.send_flag = '1账号未授权或已删除'
                isOk=False
            else:
                amclaItem.send_flag = '0'

            amclaItem.save()

        obj.status = '0' if isOk else '4'
        obj.save()

        return None


    @list_route(methods=['GET'])
    @Core_connector()
    def AccUserCount_get(self, request, *args, **kwargs):

        return {"data":{"count":AccLinkUser.objects.filter(accid__in=request.query_params_format.get("accids",[]),umark='0').count()}}

    @list_route(methods=['GET'])
    @Core_connector()
    def AccMsgMouldMould_get(self, request, *args, **kwargs):

        return {"data":MouldMsg(accid=request.query_params_format.get("accid",0)).get_list()}

    @list_route(methods=['PUT'])
    @Core_connector(isTransaction=True)
    def AccMsgMould_upd(self,request,*args,**kwargs):

        skip_type = request.data_format.get("skip_type", None)

        if skip_type:
            if skip_type == '0':
                mould_skip = "{}{}".format('0', request.data_format.get("skip_url", ""))
            else:
                mould_skip = "{}{}||{}".format('1', request.data_format.get("skip_appid", ""),
                                               request.data_format.get("skip_pagepath", ""))
        else:
            mould_skip = ""

        try:
            obj = AccMsgMould.objects.get(id=request.data_format.get("id"))
        except AccMsgMould.DoesNotExist:
            raise PubErrorCustom("无此信息!")

        obj.accid = request.data_format.get("accid",0)
        obj.name = request.data_format.get("name","")
        obj.mould_id=request.data_format.get("mould_id", "")
        # obj.mould_data=json.loads()
        obj.sendtime=request.data_format.get("sendtime", 0)
        obj.type=request.data_format.get("type", "")
        obj.mould_skip=mould_skip
        obj.select_sex=request.data_format.get("select_sex", "")
        obj.select_tags=request.data_format.get("select_tags", "")

        templateObj = MouldMsg(accid=obj.accid).get_list(template_id=obj.mould_id)
        if not templateObj:
            raise PubErrorCustom("无此模板!")

        obj.mould_data = json.dumps({
            "data":request.data_format.get("mould_data", {}),
            "templateObj":templateObj
        })

        obj.mould_name = templateObj['title']

        obj.save()

        MsgMould().sendtask_upd(obj=AccMsgMouldModelSerializer1(obj,many=False).data)

        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccMsgMould_add(self, request, *args, **kwargs):

        skip_type = request.data_format.get("skip_type", None)
        accid = request.data_format.get("accid", 0)
        if skip_type:
            if skip_type == '0':
                mould_skip = "{}{}".format('0', request.data_format.get("skip_url", ""))
            else:
                mould_skip = "{}{}||{}".format('1', request.data_format.get("skip_appid", ""),
                                               request.data_format.get("skip_pagepath", ""))
        else:
            mould_skip = ""

        templateObj = MouldMsg(accid=accid).get_list(template_id=request.data_format.get("mould_id", ""))
        if not templateObj:
            raise PubErrorCustom("无此模板!")

        obj = AccMsgMould.objects.create(**dict(
            accid=accid,
            name=request.data_format.get("name", ""),
            mould_id=request.data_format.get("mould_id", ""),
            mould_data=json.dumps({
                                    "data":request.data_format.get("mould_data", {}),
                                    "templateObj":templateObj
                                }),
            mould_name=templateObj['title'],
            sendtime=request.data_format.get("sendtime", 0),
            type=request.data_format.get("type", ""),
            mould_skip=mould_skip,
            select_sex=request.data_format.get("select_sex", ""),
            select_tags=request.data_format.get("select_tags", ""),
        ))

        MsgMould().sendtask_add(obj=AccMsgMouldModelSerializer1(obj,many=False).data)

        return None

    @list_route(methods=['DELETE'])
    @Core_connector(isTransaction=True)
    def AccMsgMould_del(self, request, *args, **kwargs):

        AccMsgMould.objects.filter(id=request.data_format.get("id")).delete()
        MsgMould().sendtask_del(request.data_format.get("id"))

        return None

    @list_route(methods=['GET'])
    @Core_connector(isPagination=True)
    def AccMsgMouldList_get(self, request, *args, **kwargs):

        query = AccMsgMould.objects.filter()

        status = request.query_params_format.get("status",None)

        if status:
            query = query.filter(status=status)

        count = query.count()

        return {"data": AccMsgMouldSerializer(query[request.page_start:request.page_end], many=True).data, "count": count}

    @list_route(methods=['GET'])
    @Core_connector()
    def AccMsgMould_get(self, request, *args, **kwargs):

        query = AccMsgMould.objects.get(id=request.query_params_format.get("id", 0))
        return {"data": AccMsgMouldModelSerializer(query, many=False).data}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccMsgMould_Send(self, request, *args, **kwargs):

        try:
            obj = AccMsgMould.objects.get(id=request.data_format.get("id"))
        except AccMsgMould.DoesNotExist:
            raise PubErrorCustom("无此信息!")

        query_format=str()
        query_params=list()

        query_format = query_format + " and t1.accid =%d"
        query_params.append(obj.accid)

        if obj.type == '1':
            select_tags = json.loads(obj.select_tags)
            if len(select_tags):
                query_format = query_format + " and ("
                for j,item in enumerate(select_tags):
                    if j>0:
                        query_format = query_format + " or "

                    query_format = query_format + " (t1.tags like %s or t1.tags like %s)"
                    query_params.append("%,{}%".format(item))
                    query_params.append("%{},%".format(item))

                query_format = query_format + " )"
        elif obj.type == '2':
            if obj.select_sex in ['0','1','2']:
                query_format = query_format + " and t1.sex =%s"
                query_params.append(obj.select_sex)

        res = AccLinkUser.objects.raw("""
            SELECT t1.* FROM acclinkuser as t1
            WHERE t1.umark='0' %s
        """% (query_format), query_params)

        for aluItem in res:
            try:
                """
                obj.content.replace("<粉丝昵称>",user['nickname'])
                """
                mould_data=json.loads(obj.mould_data['data'])
                for key in mould_data:
                    mould_data[key]['value'] = mould_data['key']['value'].replace("<粉丝昵称>",aluItem.nickname)
                data = {
                    "touser": aluItem.openid,
                    "template_id": obj.mould_id,
                    "data":mould_data
                }
                if len(obj.mould_skip):
                    if obj.mould_skip[0] == '0':
                        data['url'] = obj.mould_skip[1:]
                    else:
                        data['miniprogram'] = {
                            "appid": obj.mould_skip[1:].split("||")[0],
                            "pagepath":obj.mould_skip[1:].split("||")[1]
                        }
                MouldMsg(accid=obj.accid).send_msg(data)
                obj.send_count+=1
            except Exception as e:
                logger.error(str(e))

        obj.status = '0'
        obj.save()
        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True)
    def AccMsgMass_add(self,request,*args,**kwargs):

        obj = AccMsgMass.objects.create(**dict(
            accid=request.data_format.get('accid'),
            sendtime=request.data_format.get('sendtime'),
            type=request.data_format.get('type'),
            select_sex=request.data_format.get("select_sex",""),
            select_followtime=request.data_format.get("select_followtime",""),
            select_province=request.data_format.get("select_province", ""),
            select_city=request.data_format.get("select_city", ""),
            select_tags=json.dumps(request.data_format.get("select_tags", [])),
            power=request.data_format.get("power"),
            repeat_send=request.data_format.get("repeat_send"),
            mobile=request.data_format.get("mobile",""),
            msgtype=request.data_format.get('lists')[0]['type']
        ))

        obj.listids = json.loads(obj.listids)

        customMsgListAdd(obj,request.data_format.get('lists'),isHaveNewsList=False)

        obj.listids = json.dumps(obj.listids)

        obj.save()

        MsgMass().sendtask_add(obj=AccMsgMassModelSerializer1(obj,many=False).data)

        return None

    @list_route(methods=['PUT'])
    @Core_connector(isTransaction=True)
    def AcMsgMass_upd(self,request):

        try:
            obj = AccMsgMass.objects.get(id=request.data_format.get("id"))
        except AccMsgMass.DoesNotExist:
            raise PubErrorCustom("无此信息!")

        obj.accid = request.data_format.get('accid')
        obj.sendtime = request.data_format.get('sendtime')
        obj.type = request.data_format.get('type')
        obj.select_sex = request.data_format.get("select_sex", "")
        obj.select_followtime = request.data_format.get("select_followtime", "")
        obj.select_province = request.data_format.get("select_province", "")
        obj.select_city = request.data_format.get("select_city", "")
        obj.select_tags = json.dumps(request.data_format.get("select_tags", []))
        obj.power = request.data_format.get("power")
        obj.repeat_send = request.data_format.get("repeat_send")
        obj.mobile = request.data_format.get("mobile", "")
        obj.msgtype = request.data_format.get('lists')[0]['type']

        customMsgListUpd(obj,request.data_format.get('lists'),isHaveNewsList=False)

        obj.listids = json.dumps(obj.listids)
        obj.save()

        MsgMass().sendtask_upd(obj=AccMsgMassModelSerializer1(obj,many=False).data)

        return None

    @list_route(methods=['DELETE'])
    @Core_connector(isTransaction=True)
    def AccMsgMass_del(self, request):
        AccMsgMass.objects.filter(id=request.data_format.get("id")).delete()
        MsgMass().sendtask_del(request.data_format.get("id"))
        return None

    @list_route(methods=['GET'])
    @Core_connector(isPagination=True)
    def AccMassList_get(self, request, *args, **kwargs):

        ut = UtilTime()

        query = AccMsgMass.objects.filter()

        date = request.query_params_format.get("date", None)

        status = request.query_params_format.get("status", None)

        if date:
            start = ut.string_to_timestamp(date+' 00:00:01')
            end = ut.string_to_timestamp(date+' 23:59:59')
            query = query.filter(sendtime__gte=start, senditme__lte=end)

        if status:
            query = query.filter(status=status)

        count = query.count()

        return {"data": AccMsgMassSerializer(query[request.page_start:request.page_end], many=True).data,
                "count": count}

    @list_route(methods=['GET'])
    @Core_connector()
    def AccMassDetail_get(self, request, *args, **kwargs):
        try:
            obj = AccMsgMass.objects.get(id=request.query_params_format.get("id"))
        except AccMsgMass.DoesNotExist:
            raise PubErrorCustom("无此信息!")

        aqlObj = AccQrcodeList.objects.get(id=json.loads(obj.listids)[0])
        if aqlObj.type != '1':
            return {"data":AccQrcodeListModelSerializer1(aqlObj,many=False).data}
        else:
            response = WechatMaterial(accid=obj.accid).get_forever(
                media_id=aqlObj.media_id
            )
            return {"data":response}

    @list_route(methods=['GET'])
    @Core_connector()
    def AccMass_get(self, request, *args, **kwargs):

        try:
            return {"data":AccMsgMassModelSerializer(AccMsgMass.objects.get(id=request.query_params_format.get("id")),many=False).data}
        except AccMsgMass.DoesNotExist:
            raise PubErrorCustom("无此信息!")

    @list_route(methods=['POST'])
    @Core_connector()
    def AccMass_Send(self, request, *args, **kwargs):
        try:
            obj = AccMsgMass.objects.get(id=request.data_format.get("id"))
        except AccMsgMass.DoesNotExist:
            raise PubErrorCustom("无此信息!")

        query_format=str()
        query_params=list()

        query_format = query_format + " and t1.accid =%d"
        query_params.append(obj.accid)

        if obj.type != '1':
            if obj.select_sex in ['0', '1', '2']:
                query_format = query_format + " and t1.sex =%s"
                query_params.append(obj.select_sex)
            if len(obj.select_followtime):
                start = obj.select_followtime.split('-')[0]
                end = obj.select_followtime.split('-')[1]
                query_format = query_format + " and t1.subscribe_time>=%s and t1.subscribe_time<=%s"
                query_params.append(start)
                query_params.append(end)
            if len(obj.select_province):
                query_format = query_format + " and t1.province=%s"
                query_params.append(obj.select_province)
            if len(obj.select_city):
                query_format = query_format + " and t1.city=%s"
                query_params.append(obj.select_city)

            select_tags = json.loads(obj.select_tags)
            if len(select_tags):
                query_format = query_format + " and ("
                for j, item in enumerate(select_tags):
                    if j > 0:
                        query_format = query_format + " or "

                    query_format = query_format + " (t1.tags like %s or t1.tags like %s)"
                    query_params.append("%,{}%".format(item))
                    query_params.append("%{},%".format(item))

                query_format = query_format + " )"

        res = AccLinkUser.objects.raw("""
            SELECT t1.* FROM acclinkuser as t1
            WHERE t1.umark='0' %s
        """% (query_format), query_params)
        openids = [ item.openid for item in res]
        obj.send_count = len(openids)
        MsgMass().send_msg(
            openids=openids,
            accid=obj.accid,
            listids=obj.listids,
            is_to_all=True if obj.power=='0' else False,
            send_ignore_reprint= 1 if obj.repeat_send=='0' else 0 )

        obj.status = '0'
        obj.save()
        return None

    @list_route(methods=['GET','POST'])
    @Core_connector(isReturn=True)
    def test(self,request, *args, **kwargs):

        Follow().sendtask(
            {
                "sendlimit": 1,
                "listids": [1,2],
            },
            nickname="nickname",
            openid="openid",
            accid=2
        )
        return HttpResponse("ok")


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
