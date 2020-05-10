
import hashlib



class CustomBase(object):

    def __init__(self,**kwargs):
        self.appid = "123"


class CustomAuthorize(CustomBase):

    def authorizeUrl(self):

        redirect_uri=""

        url = """
        https://open.weixin.qq.com/connect/oauth2/authorize?appid={}&redirect_uri={}&response_type=code&scope=snsapi_userinfo&state=State#wechat_redirect
        """.format(self.appid,redirect_uri)

        return url



# class CustomHash(object):
#
#
#     def __init__(self,**kwargs):
#         pass
#         self.token = kwargs.get("token",None)
#
#     def tokenCheck(self,timestamp, nonce,signature):
#
#         sortlist = [self.token, timestamp, nonce]
#         sortlist.sort()
#         sha = hashlib.sha1()
#         sha.update("".join(sortlist).encode("utf8"))
#         newsignature = sha.hexdigest()
#
#         print("{},{}".format(signature,newsignature))
#         if newsignature != signature:
#             return False
#         else:
#             return True