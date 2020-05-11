from django.db import models

from lib.utils.mytime import UtilTime

class Acc(models.Model):

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

    class Meta:
        verbose_name = '公众号列表'
        verbose_name_plural = verbose_name
        db_table = 'acc'