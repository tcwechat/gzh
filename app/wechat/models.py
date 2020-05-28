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

    synctime = models.BigIntegerField(default=0,verbose_name="上次同步粉丝列表时间")

    follow_setting = models.CharField(max_length=1,verbose_name="关注设置标志:'0'-设置,'1'-未设置",default='1')

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

    headimgurl= models.CharField(max_length=255,verbose_name="头像",default="")
    nickname = models.CharField(max_length=60,verbose_name="昵称",default="")
    sex = models.CharField(max_length=1,verbose_name="用户的性别，值为1时是男性，值为2时是女性，值为0时是未知",default="")
    subscribe_time = models.BigIntegerField(default=0,verbose_name="关注时间")
    city =models.CharField(max_length=60,verbose_name="城市",default="")
    country = models.CharField(max_length=60,verbose_name="国家",default="")
    province = models.CharField(max_length=60,verbose_name="省份",default="")
    subscribe_scene = models.CharField(max_length=60,verbose_name="ADD_SCENE_SEARCH 公众号搜索，ADD_SCENE_ACCOUNT_MIGRATION 公众号迁移，ADD_SCENE_PROFILE_CARD 名片分享，ADD_SCENE_QR_CODE 扫描二维码，ADD_SCENE_PROFILE_LINK 图文页内名称点击，ADD_SCENE_PROFILE_ITEM 图文页右上角菜单，ADD_SCENE_PAID 支付后关注，ADD_SCENE_OTHERS 其他",default="")
    memo = models.CharField(max_length=60,verbose_name="备注",default="")

    umark = models.CharField(max_length=1,verbose_name="状态 0-正常,1-删除",default='0')

    last_active_time = models.BigIntegerField(default=0,
                                              verbose_name="""
                                              上次活跃时间
                                              (包括粉丝发送消息给公众号、 点击自定义菜单、关注公众号、
                                               扫描二维码、 支付成功、用户维权等，阅读公众号文章不算互动） 的粉丝数。
                                              """)

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

    umark = models.CharField(max_length=1, verbose_name="状态 0-正常,1-删除", default='0')

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

    listids = models.CharField(max_length=1024,verbose_name="推送内容id集合",default='[]')

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


class AccFollow(models.Model):
    """
    关注回复
    """

    id = models.BigAutoField(primary_key=True)
    accid = models.BigIntegerField(verbose_name="公众号ID")
    send_type = models.CharField(max_length=1,verbose_name="推送方式:0-全部推送,1-按顺序推送,2-随机推送一条",default="0")
    send_limit = models.IntegerField(default=0,verbose_name="按顺序推送  每条间隔的时间,单位小时")
    listids = models.CharField(max_length=1024,verbose_name="推送内容id集合",default='[]')
    createtime = models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):

        ut =  UtilTime()
        if not self.createtime:
            self.createtime = ut.timestamp
        return super(AccFollow, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '关注回复'
        verbose_name_plural = verbose_name
        db_table = 'accfollow'


class AccQrcodeList(models.Model):
    """
    渠道二维码推送内容
    """

    id = models.BigAutoField(primary_key=True)
    qrid = models.BigIntegerField(verbose_name="二维码ID")
    type = models.CharField(max_length=1,verbose_name="类型,1-图文,2-图片,3-文字,4-音频,5-视频")

    iamgetextids = models.CharField(max_length=1024,default="[]",verbose_name="图文列表ID")

    media_id = models.CharField(max_length=60,verbose_name="媒体ID/图文推送内容ID",default="")
    content = models.TextField(verbose_name="文字内容",default="")

    sort = models.IntegerField(default=0)

    class Meta:
        verbose_name = '渠道二维码推送内容'
        verbose_name_plural = verbose_name
        db_table = 'accqrcodelist'

class AccQrcodeImageTextList(models.Model):
    """
    渠道二维码图文推送内容
    """

    id = models.BigAutoField(primary_key=True)
    qr_listid = models.BigIntegerField(verbose_name="二维码推送内容ID")

    picurl = models.CharField(max_length=255,verbose_name="资源链接")
    media_id = models.CharField(max_length=60, verbose_name="媒体ID/资源链接", default="")
    url = models.CharField(max_length=255,verbose_name="点击图文跳转的链接")
    title = models.CharField(max_length=255,verbose_name="标题")
    description = models.TextField(verbose_name="描述,文字消息时,用此处值")

    sort = models.IntegerField(default=0)

    class Meta:
        verbose_name = '渠道二维码图文推送内容'
        verbose_name_plural = verbose_name
        db_table = 'accqrcodeimagetextlist'

