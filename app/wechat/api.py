
import json
import xml.etree.cElementTree as ET

from rest_framework import viewsets
from lib.core.decorator.response import Core_connector
from rest_framework.decorators import list_route,detail_route
from django.shortcuts import HttpResponse

from lib.utils.wechat.ticket import WechatMsgValid
from lib.utils.wechat.msg import WechatAccMsg
from lib.utils.wechat.base import WechatBaseForUser
from lib.utils.wechat.qrcode import WechatQrcode
from lib.utils.db import RedisTicketHandler

from app.wechat.models import Acc,AccTag as AccTagModel,AccQrcode as AccQrcodeModel,AccQrcodeList
from lib.utils.exceptions import PubErrorCustom

from app.wechat.serialiers import AccSerializer,AccTagModelSerializer

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
                # service_type_info=json.dumps(authorizer_info['service_type_info']),
                # verify_type_info=json.dumps(authorizer_info['verify_type_info']),
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

        # cH = WechatMsgValid()
        #
        # # if not cH.check_appid(pk):
        # #     raise PubErrorCustom("非法请求!{}".format(pk))
        # print(cH.run())
        # print(request.body.decode('utf-8'))

        WechatAccMsg(
            timestamp=request.query_params['timestamp'],
            nonce=request.query_params['nonce'],
            signature=request.query_params['msg_signature'],
            xmlc=request.body.decode('utf-8')
        ).eventHandler()

        return HttpResponse("success")


    @list_route(methods=['GET'])
    @Core_connector(isTicket=True)
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
    @Core_connector(isTransaction=True)
    def AccTag(self,request,*args,**kwargs):

        if request.method =='POST':
            obj = AccTagModel.objects.create(**dict(
                name = request.data_format.get("name"),
                accid = request.data_format.get("accid")
            ))
            return {"data":{"id":obj.id}}
        elif request.method =='PUT':
            try:
                obj = AccTagModel.objects.get(id=request.data_format.get("id"))
                obj.name = request.data_format.get("name")
                obj.save()
            except AccTagModel.DoesNotExist:
                raise PubErrorCustom("不存在此标签!")
        elif request.method == 'DELETE':
            AccTagModel.objects.filter(id=request.data_format.get("id")).delete()
        elif request.method == 'GET':
            return { "data":AccTagModelSerializer(AccTagModel.objects.filter(accid=request.query_params_format.get("accid")),many=True).data}
        else:
            raise PubErrorCustom("拒绝访问!")

        return None

    @list_route(methods=['POST','GET','PUT','DELETE'])
    @Core_connector(isTransaction=True)
    def AccQrcode(self,request,*args,**kwargs):

        if request.method == 'POST':

            obj = AccQrcodeModel.objects.create(**dict(
                name = request.data_format.get('name'),
                accid = request.data_format.get('accid'),
                type=request.data_format.get('type'),
                qr_type=request.data_format.get('qr_type'),
                send_type=request.data_format.get('send_type'),
                tags=json.dumps(request.data_format.get('tags')),
            ))

            aql_objs=[]
            for item in request.data_format.get('contents'):
                aql_objs.append(AccQrcodeList.objects.create(**dict(
                    type=item.get("item"),
                    picurl=item.get("picurl",""),
                    url=item.get("url",""),
                    title=item.get("title", ""),
                    description=item.get("description", "")
                )))

            if obj.type == '0':
                obj.url = WechatQrcode(accid=obj.accid).qrcode_create(obj.id)
            else:
                obj.url = WechatQrcode(accid=obj.accid).qrcode_create_forever(obj.id)

            obj.save()
        return None


    @detail_route(methods=['POST'])
    @Core_connector(isReturn=True)
    def test(self,request, *args, **kwargs):

        pk= kwargs.get("pk")

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
