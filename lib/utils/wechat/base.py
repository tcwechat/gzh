
import base64,hashlib
import xml.etree.cElementTree as ET

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

        self.xml_tree = ET.fromstring(kwargs.get("xmltext",None)) if kwargs.get("xmltext",None) else None

        try:
            self.key = base64.b64decode("FDl8GfVXfGWwKs9LKc11xE6N2f8DM6MB8cyMm6xYsac" + "=")
            assert len(self.key) == 32
        except Exception:
            throw_exception("[error]: EncodingAESKey unvalid !",
                            FormatException)

    def sha1(self,sortlist):
        sortlist.sort()
        sha = hashlib.sha1()
        sha.update("".join(sortlist).encode("utf8"))
        return sha.hexdigest()
