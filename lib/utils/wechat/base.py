
import base64,hashlib,json
import xml.etree.cElementTree as ET
from lib.utils.db import RedisAccessTokenHandler,RedisTicketHandler
from requests import request

class FormatException(Exception):
    pass

def throw_exception(message, exception_class=FormatException):
    """my define raise exception function"""
    raise exception_class(message)

class WechatBase(object):

    def __init__(self,**kwargs):
        """
            # @param token: 公众平台上，开发者设置的Token
            # @param key: 公众平台上，开发者设置的EncodingAESKey
            # @param appid: 企业号的AppId
        """
        self.token = "eNoUNRR4e7V85KLb"
        self.appid = "wxbc8cf6d177029077"
        self.secret = "cad9594114c9473b5d9a697cfe154b33"

        self.xml_tree = ET.fromstring(kwargs.get("xmltext",None)) if kwargs.get("xmltext",None) else None

        if kwargs.get("isAccessToken",None):
            self.accesstoken = self.getAccessToken()

        try:
            self.key = base64.b64decode("FDl8GfVXfGWwKs9LKc11xE6N2f8DM6MB8cyMm6xYsac" + "=")
            assert len(self.key) == 32
        except Exception:
            throw_exception("[error]: EncodingAESKey unvalid !",
                            FormatException)

    def getAccessToken(self):
        t = RedisAccessTokenHandler()

        res = t.get()
        if not res:
            response  = request(method="POST",url="https://api.weixin.qq.com/cgi-bin/component/api_component_token",json={
                "component_appid": self.appid,
                "component_appsecret": self.secret,
                "component_verify_ticket":  RedisTicketHandler().get()
            })
            print(response.text)
            response = json.loads(response.content.decode('utf-8'))
            t.set(response['component_access_token'],response['expires_in'])
            return response['component_access_token']
        else:
            return res

    def sha1(self,sortlist):
        sortlist.sort()
        sha = hashlib.sha1()
        sha.update("".join(sortlist).encode("utf8"))
        return sha.hexdigest()
