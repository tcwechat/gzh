
import hashlib,json
from project.config_include.params import TX_WECHAT_TOKEN

from lib.utils.wechat.user import WeChatAccTag

from app.wechat.models import AccTag,AccQrcodeList,AccQrcodeImageTextList,AccActionCount,AccCount
from app.public.models import Meterial

from lib.utils.exceptions import PubErrorCustom
from lib.utils.log import logger


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


def tag_del(query,tagid,accid):
    openids = []
    valid_count = 0
    for item in query:
        tags = json.loads(item.tags)

        if tagid in tags:
            tags.remove(tagid)
            item.tags = json.dumps(tags).replace(" ", "")
            item.save()
            valid_count += 1
        openids.append(item.openid)

    WeChatAccTag(accid=accid).delete(id=tagid)

def tag_canle(query,tagid,accid):

    openids = []
    valid_count = 0
    for item in query:
        tags = json.loads(item.tags)

        if tagid in tags:
            tags.remove(tagid)
            item.tags = json.dumps(tags).replace(" ", "")
            item.save()
            valid_count += 1
        openids.append(item.openid)

    if valid_count:
        try:
            atmObj = AccTag.objects.select_for_update().get(id=tagid)
            atmObj.fans_count -= valid_count
            atmObj.wechat_fans_count -= valid_count
            atmObj.save()
        except AccTag.DoesNotExist:
            raise PubErrorCustom("无此标签!")

    if len(openids):
        WeChatAccTag(accid=accid).batchtagging_canle(openids, int(tagid))


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

def countHandlerEx(**kwargs):

    data = kwargs.get("data")
    tot_fs_num = kwargs.get("tot_fs_num")
    num = kwargs.get("num")

    r_data={
        "xgz_num":0,
        "qg_num":0,
        "qg_rate":0.0,
        "jz_num":0,
        "zz_agree":0
    }

    count = 0
    for item in data:
        r_data['xgz_num'] += item['xgz_num']
        r_data['qg_num'] += item['qg_num']
        r_data['jz_num'] += item['jz_num']
        r_data['qg_rate'] += item['qg_rate']
        count+=1

    r_data['qg_rate'] = round(r_data['qg_rate'] * 1.0 / count if count else 0.0,2)
    r_data['zz_agree'] = int(r_data['xgz_num'] / num) if num else 0

    return r_data

def countHandler(**kwargs):



    accid = kwargs.get("accid")
    time = kwargs.get("time")
    start = kwargs.get("start")
    end = kwargs.get("end")
    tot_fs_num = kwargs.get("tot_fs_num")

    isday = kwargs.get("isday",None)

    ut = kwargs.get("ut")

    res = {
        "time": time,
        "xgz_num": 0,
        "qg_num": 0,
        "qg_rate": 0.0,
        "jz_num": 0,
        "tot_fs_num":0
    }

    for item in AccActionCount.objects.filter(accid=accid, action__in=['1', '3'],
                                              createtime__gte=start,
                                              createtime__lte=end):

        try:
            tot_fs_num_tmp = AccCount.objects.get(accid=accid,date=ut.timestamp_to_string(item.createtime)[:10]).tot_fs_num
            tot_fs_num=tot_fs_num_tmp
        except AccCount.DoesNotExist:
            pass

        if item.action == '1':
            res['xgz_num'] += 1
        elif item.action == '3':
            res['qg_num'] += 1

        res['qg_rate'] = round(res['qg_num'] * 100 / (tot_fs_num + res['qg_num']) if tot_fs_num + res['qg_num'] else 0.0,2)
        res['jz_num'] = res['xgz_num'] - res['qg_num']

        if isday:
            res['tot_fs_num'] = tot_fs_num

    return res


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