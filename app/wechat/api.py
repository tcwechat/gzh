

from rest_framework import viewsets
from lib.core.decorator.response import Core_connector
from rest_framework.decorators import list_route


from app.wechat.utils import CustomHash

class WeChatAPIView(viewsets.ViewSet):

    @list_route(methods=['GET'])
    @Core_connector()
    def initCheck(self,request, *args, **kwargs):
        print(request.query_params_format)
        signature = request.query_params_format.get("signature",None)
        timestamp = request.query_params_format.get("timestamp",None)
        nonce = request.query_params_format.get("nonce",None)
        echostr = request.query_params_format.get("echostr",None)


        token="b3aa7790500908e9a9e454b4fd1d126f"
        encrypt="b3aa7790500908e9a9e454b4fd1d126f"

        if CustomHash(token=token).tokenCheck(nonce=nonce,timestamp=timestamp,signature=signature):
            return echostr
        else:
            return ""
