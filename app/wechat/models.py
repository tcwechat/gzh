from django.db import models

from lib.utils.mytime import UtilTime

class Acc(models.Model):

    """
    公众号列表
    """

    accid=models.BigAutoField(primary_key=True)

    authorizer_appid = models.CharField(max_length=60,verbose_name="授权方appid")
    authorizer_refresh_token = models.CharField(max_length=60,verbose_name="刷新令牌")

    nick_name = models.CharField(max_length=60,verbose_name="昵称",default="")
    head_img = models.CharField(max_length=255,verbose_name="头像",default="")
    service_type_info  = models.CharField(max_length=255,verbose_name="公众号类型",default="{}")
    verify_type_info  = models.CharField(max_length=255,verbose_name="公众号认证类型",default="{}")

    user_name = models.CharField(max_length=60,verbose_name="原始ID",default="")
    principal_name = models.CharField(max_length=60,verbose_name="主体名称",default="")
    alias = models.CharField(max_length=60,verbose_name="公众号所设置的微信号，可能为空",default="")
    business_info = models.CharField(max_length=255,verbose_name="用以了解功能的开通状况（0代表未开通，1代表已开通）",default="{}")
    qrcode_url = models.CharField(max_length=255,verbose_name="二维码图片的 URL，开发者最好自行也进行保存",default="")


    createtime=models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):

        if not self.createtime:
            self.createtime = UtilTime().timestamp
        return super(Acc, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '公众号列表'
        verbose_name_plural = verbose_name
        db_table = 'acc'


class AccLinkUser(models.Model):

    """
    公众号用户关联表
    """

    id=models.BigAutoField(primary_key=True)
    accid = models.BigIntegerField(verbose_name="公众号ID")
    openid = models.CharField(max_length=60,verbose_name="粉丝openid")
    tags = models.CharField(max_length=1024, verbose_name="标签集合", default="[]")
    createtime=models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):

        if not self.createtime:
            self.createtime = UtilTime().timestamp
        return super(AccLinkUser, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '公众号用户关联表'
        verbose_name_plural = verbose_name
        db_table = 'acclinkuser'



class AccTag(models.Model):
    """
    标签
    """

    id = models.BigAutoField(primary_key=True)

    name = models.CharField(max_length=60,default="",verbose_name="标签名字")
    accid = models.BigIntegerField(verbose_name="公众号ID")
    fans_count = models.IntegerField(default=0,verbose_name="粉丝数量")

    wechat_fans_count = models.IntegerField(default=0,verbose_name="微信粉丝数量")

    createtime = models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):

        ut =  UtilTime()
        if not self.createtime:
            self.createtime = ut.timestamp
        return super(AccTag, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = verbose_name
        db_table = 'acctag'


class AccQrcode(models.Model):
    """
    渠道二维码
    """

    id = models.BigAutoField(primary_key=True)

    name = models.CharField(max_length=60,default="",verbose_name="二维码名称")
    accid = models.BigIntegerField(verbose_name="公众号ID")
    tot_count = models.IntegerField(verbose_name="总扫码次数(既扫码也关注)",default=0)
    new_count = models.IntegerField(verbose_name="新扫码且关注",default=0)
    follow_count = models.IntegerField(verbose_name="已关注扫码",default=0)
    type = models.CharField(max_length=1,verbose_name="类型,0-临时,1-永久",default="1")
    endtime = models.BigIntegerField(default=0)

    qr_type = models.CharField(max_length=1,verbose_name="扫码推送:0-新建扫码推送消息,1-不启用",default="0")

    tags = models.CharField(max_length=1024,verbose_name="标签集合",default="[]")

    send_type = models.CharField(max_length=1,verbose_name="推送方式:0-随机推送一条,1-全部推送",default="0")

    url = models.CharField(max_length=255,verbose_name="二维码链接",default="")

    createtime = models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):

        ut =  UtilTime()
        if not self.createtime:
            self.createtime = ut.timestamp
        if self.type == '0':
            self.endtime = ut.today.shift(days=30).timestamp
        return super(AccQrcode, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '渠道二维码'
        verbose_name_plural = verbose_name
        db_table = 'accqrcode'


class AccQrcodeList(models.Model):
    """
    渠道二维码内容明细
    """

    id = models.BigAutoField(primary_key=True)

    qrid = models.BigIntegerField(verbose_name="二维码ID")

    type = models.CharField(max_length=1,verbose_name="类型,0-图文,1-图片,2-文字,3-音频,4-视频")





    class Meta:
        verbose_name = '渠道二维码内容明细'
        verbose_name_plural = verbose_name
        db_table = 'accqrcodelist'