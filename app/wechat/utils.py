
import hashlib


class CustomHash(object):


    def __init__(self,**kwargs):
        pass
        self.token = kwargs.get("token",None)


    def tokenCheck(self,timestamp, nonce,signature):

        sortlist = [self.token, timestamp, nonce]
        sortlist.sort()
        sha = hashlib.sha1()
        sha.update("".join(sortlist).encode("utf8"))
        newsignature = sha.hexdigest()

        print("{},{}".format(signature,newsignature))
        if newsignature != signature:
            return False
        else:
            return True