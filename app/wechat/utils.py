
import hashlib,json
from project.config_include.params import TX_WECHAT_TOKEN

from lib.utils.wechat.user import WeChatAccTag

from app.wechat.models import AccTag,AccQrcodeList,AccQrcodeImageTextList
from app.public.models import Meterial

from lib.utils.exceptions import PubErrorCustom


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

def tag_batchtagging(query,tagid,accid):

    openids = []
    valid_count = 0
    for item in query:
        tags = json.loads(item.tags)

        if tagid not in tags:
            tags.append(tagid)
            item.tags = json.dumps(tags).replace(" ", "")
            item.save()
            valid_count += 1
        openids.append(item.openid)

    if valid_count:
        try:
            atmObj = AccTag.objects.select_for_update().get(id=tagid)
            atmObj.fans_count += valid_count
            atmObj.wechat_fans_count += valid_count
            atmObj.save()
        except AccTag.DoesNotExist:
            raise PubErrorCustom("无此标签!")

    if len(openids):
        WeChatAccTag(accid=accid).batchtagging(openids, int(tagid))


def customMsgListAdd(obj,lists,isHaveNewsList=True):

    for c, item in enumerate(lists):
        aqlObj = AccQrcodeList.objects.create(**dict(
            type=item.get("type"),
            qrid=obj.id,
            media_id=item.get("media_id", ""),
            url = item.get("url",""),
            content=item.get("content", ""),
            sort=c + 1
        ))
        obj.listids.append(aqlObj.id)

        if isHaveNewsList:
            if str(item.get("type")) == '1':
                aqlObj.iamgetextids = json.loads(aqlObj.iamgetextids)
                for j, cItem in enumerate(item.get("imagetextlist")):
                    # try:
                    #     mObj = Meterial.objects.get(media_id=cItem.get("media_id", ""))
                    # except Meterial.DoesNotExist:
                    #     raise PubErrorCustom("无此媒体数据{}".format(cItem.get("media_id", "")))

                    aqitlObj = AccQrcodeImageTextList.objects.create(**dict(
                        qr_listid=aqlObj.id,
                        picurl=cItem.get("picurl", ""),
                        media_id=cItem.get("media_id", ""),
                        url=cItem.get("url", ""),
                        title=cItem.get("title", ""),
                        description=cItem.get("description", ""),
                        sort=j + 1
                    ))
                    aqlObj.iamgetextids.append(aqitlObj.id)

                aqlObj.iamgetextids = json.dumps(aqlObj.iamgetextids)
                aqlObj.save()


def customMsgListUpd(obj,lists,isHaveNewsList=True):

    for c, item in enumerate(lists):
        if item.get("id", None):
            try:
                aqlObj = AccQrcodeList.objects.get(id=item.get("id", None))
            except AccQrcodeList.DoesNotExist:
                raise PubErrorCustom("无此内容明细!")
            aqlObj.type = item.get("type")
            aqlObj.qrid = obj.id
            aqlObj.media_id = item.get("media_id", "")
            aqlObj.url = item.get("url", "")
            aqlObj.content = item.get("content", "")
            aqlObj.sort = c + 1
        else:
            aqlObj = AccQrcodeList.objects.create(**dict(
                type=item.get("type"),
                qrid=obj.id,
                media_id=item.get("media_id", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                sort=c + 1
            ))

        obj.listids.append(aqlObj.id)

        if isHaveNewsList:
            if item.get("type") == '1':
                aqlObj.iamgetextids = []
                for j, cItem in enumerate(item.get("imagetextlist")):

                    # try:
                    #     mObj = Meterial.objects.get(media_id=cItem.get("media_id", ""))
                    # except Meterial.DoesNotExist:
                    #     raise PubErrorCustom("无此媒体数据{}".format(cItem.get("media_id", "")))

                    if cItem.get("id", None):
                        try:
                            aqitlObj = AccQrcodeImageTextList.objects.get(id=cItem.get("id", None))
                        except AccQrcodeImageTextList.DoesNotExist:
                            raise PubErrorCustom("无此图文明细!")

                        aqitlObj.qr_listid = aqlObj.id
                        aqitlObj.picurl = cItem.get("picurl", "")
                        aqitlObj.media_id = cItem.get("media_id", "")
                        aqitlObj.url = cItem.get("url", "")
                        aqitlObj.title = cItem.get("title", "")
                        aqitlObj.description = cItem.get("description", "")
                        aqitlObj.sort = j + 1
                        aqitlObj.save()
                    else:
                        aqitlObj = AccQrcodeImageTextList.objects.create(**dict(
                            qr_listid=aqlObj.id,
                            picurl=cItem.get("picurl", ""),
                            media_id=cItem.get("media_id", ""),
                            url=cItem.get("url", ""),
                            title=cItem.get("title", ""),
                            description=cItem.get("description", ""),
                            sort=j + 1
                        ))
                    aqlObj.iamgetextids.append(aqitlObj.id)
                aqlObj.iamgetextids = json.dumps(aqlObj.iamgetextids)

        aqlObj.save()


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