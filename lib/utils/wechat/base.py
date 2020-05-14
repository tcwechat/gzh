
import base64,hashlib,json
import xml.etree.cElementTree as ET
from lib.utils.db import RedisAccessTokenHandler,RedisTicketHandler,RedisPreAuthCodeHandler,RedisAuthAccessTokenHandler
from requests import request
from app.wechat.models import Acc
from lib.utils.exceptions import PubErrorCustom

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

        try:
            self.key = base64.b64decode("FDl8GfVXfGWwKs9LKc11xE6N2f8DM6MB8cyMm6xYsac" + "=")
            assert len(self.key) == 32
        except Exception:
            throw_exception("[error]: EncodingAESKey unvalid !",
                            FormatException)

        if kwargs.get("isAccessToken",None):
            self.accesstoken = self.getAccessToken()

        if kwargs.get("accid",None):

            self.accid = kwargs.get("accid",None)

            self.auth_accesstoken = self.getAuthAccessToken()

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

    def getAuthAccessToken(self):
        t = RedisAuthAccessTokenHandler()

        res = t.get()
        if not res:

            try:
                self.acc = Acc.objects.get(accid=self.accid)
            except Acc.DoesNotExist:
                raise PubErrorCustom("该公众号不存在!{}".format(self.accid))

            response = request(method="POST", url="https://api.weixin.qq.com/cgi-bin/component/api_authorizer_token?component_access_token={}".format(self.accesstoken),
                               json={
                                   "component_appid": self.appid,
                                   "authorizer_appid": self.acc.authorizer_appid,
                                   "authorizer_refresh_token": self.acc.authorizer_refresh_token
                               })
            print(response.text)
            response = json.loads(response.content.decode('utf-8'))
            t.set(response['authorizer_access_token'], response['expires_in'])
            self.acc.authorizer_refresh_token = response['authorizer_refresh_token']
            self.acc.save()
            return response['authorizer_access_token']
        else:
            return res

    def sha1(self,sortlist):
        sortlist.sort()
        sha = hashlib.sha1()
        sha.update("".join(sortlist).encode("utf8"))
        return sha.hexdigest()

    def check_appid(self,appid):

        return appid == self.appid

class WechatBaseForUser(WechatBase):

    def __init__(self,**kwargs):

        super().__init__(isAccessToken=True,accid=kwargs.get("accid",None))

        self.pre_auth_code = self.get_pre_auth_code()

    def get_pre_auth_code(self):

        t = RedisPreAuthCodeHandler()

        res = t.get()
        if not res:
            response = request(method="POST",
                               url="https://api.weixin.qq.com/cgi-bin/component/api_create_preauthcode?component_access_token={}".format(self.accesstoken),
                               json={
                                   "component_appid": self.appid
                               })
            print(response.text)
            response = json.loads(response.content.decode('utf-8'))
            t.set(response['pre_auth_code'], response['expires_in'])
            return response['pre_auth_code']
        else:
            return res

    def get_auth_url(self):

        return """https://mp.weixin.qq.com/cgi-bin/componentloginpage?component_appid={}&pre_auth_code={}&redirect_uri={}&auth_type=1""".format(self.appid,self.pre_auth_code,"https://tc.hanggetuoke.cn/v1/api/wechat/authCallback")

    def get_auth_by_authcode(self,authorization_code):

        response = request(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/component/api_query_auth?component_access_token={}".format(
                               self.accesstoken),
                           json={
                               "component_appid": self.appid,
                               "authorization_code":authorization_code
                           })
        print(response.text)
        response = json.loads(response.content.decode('utf-8'))
        return response['authorization_info']

    def get_authorizer_info(self,authorization_info):

        response = request(method="POST",
                           url="https://api.weixin.qq.com/cgi-bin/component/api_get_authorizer_info?component_access_token={}".format(
                               self.accesstoken),
                           json={
                               "component_appid": self.appid,
                               "authorizer_appid":authorization_info['authorizer_appid']
                           })
        print(response.text)
        response = json.loads(response.content.decode('utf-8'))
        return response['authorizer_info']

    def refrech_auth_access_token(self,accid,value,expire):

        RedisAuthAccessTokenHandler(before=str(accid)).set(value,expire)
