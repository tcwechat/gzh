

from rest_framework import viewsets
from lib.core.decorator.response import Core_connector
from rest_framework.decorators import list_route
from django.shortcuts import HttpResponse

from lib.utils.wechat.ticket import WechatMsgValid
from lib.utils.wechat.base import WechatBaseForUser
from lib.utils.db import RedisTicketHandler


class WeChatAPIView(viewsets.ViewSet):

    @list_route(methods=['POST'])
    @Core_connector(isReturn=True,isRVliad=True)
    def notice(self,request, *args, **kwargs):

        ticket = WechatMsgValid(xmltext=request.body.decode('utf-8')).run(
            request.query_params['timestamp'],
            request.query_params['nonce'],
            request.query_params['msg_signature']
        )

        RedisTicketHandler().set(ticket)

        return HttpResponse("success")

    @list_route(methods=['POST'])
    @Core_connector(isReturn=True)
    def authCallback(self,request, *args, **kwargs):

        auth_code = request.query_params['auth_code']
        expires_in =  request.query_params['expires_in']

        return HttpResponse("success")

    @list_route(methods=['GET'])
    @Core_connector()
    def getPreAuthUrl(self,request):

        return {"data":WechatBaseForUser(isAccessToken=True).get_auth_url()}

    @list_route(methods=['POST'])
    @Core_connector(isReturn=True)
    def test(self,request, *args, **kwargs):

        s = WechatBaseForUser(isAccessToken=True)
        print(s.pre_auth_code)

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
