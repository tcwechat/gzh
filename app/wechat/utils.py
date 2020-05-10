
import hashlib
from project.config_include.params import TX_WECHAT_TOKEN


def requestValid(params):
    print(params)

    sortlist = [TX_WECHAT_TOKEN, params.get("timestamp"), params.get("nonce")]

    sortlist.sort()
    sha = hashlib.sha1()
    sha.update("".join(sortlist).encode("utf8"))
    newsignature = sha.hexdigest()

    print("{},{}".format(params.get("signature",None),newsignature))
    if newsignature != params.get("signature",None):
        return False
    else:
        return True



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



if __name__ == '__main__':

    signature="434450a1d34ee7866ee00ba64b2ecbca4405d3a1"

    sortlist = ["eNoUNRR4e7V85KLb", '1589126299', '1632400849']
    sortlist.sort()
    sha = hashlib.sha1()
    sha.update("".join(sortlist).encode("utf8"))
    newsignature = sha.hexdigest()

    print("{},{}".format(signature,newsignature))
    if newsignature != signature:
        print(False)
    else:
        print(True)