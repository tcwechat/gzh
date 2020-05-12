

from lib.utils.wechat.base import WechatBase
from lib.utils.wechat.WXBizMsgCrypt import WXBizMsgCrypt

class WechatAccMsg(WechatBase):

    def DecryptMsg(self,appid,timestamp,nonce,signature,xmlc):

        print(WXBizMsgCrypt(self.token,self.key,appid).DecryptMsg(
            xmlc,
            signature,
            timestamp,
            nonce
        ))

    def EncryptMsg(self):
        pass