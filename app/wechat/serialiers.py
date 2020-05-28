
import json
from rest_framework import serializers
from app.wechat.models import Acc,AccTag,AccQrcode,AccQrcodeList,AccQrcodeImageTextList,AccLinkUser,AccFollow,AccReply
from lib.utils.mytime import UtilTime
from app.public.models import Meterial
from project.config_include.common import ServerUrl
from app.public.serialiers import MeterialSerializer

class AccSerializer(serializers.Serializer):

    accid = serializers.IntegerField()
    nick_name = serializers.CharField()
    head_img = serializers.CharField()
    createtime = serializers.IntegerField()
    fans_count = serializers.SerializerMethodField()
    active_fans_count = serializers.SerializerMethodField()
    service_type = serializers.SerializerMethodField()
    verify_type = serializers.SerializerMethodField()

    def get_service_type(self,obj):
        return str(json.loads(obj.service_type_info).get("id","3"))

    def get_verify_type(self,obj):
        res = str(json.loads(obj.verify_type_info).get("id",None))

        return '0' if res and res!='-1' else '1'

    def get_active_fans_count(self,obj):

        return AccLinkUser.objects.filter(umark='0',last_active_time__gte=UtilTime().today.shift(hours=-48).timestamp).count()

    def get_fans_count(self,obj):

        return AccLinkUser.objects.filter(accid=obj.accid,umark='0').count()


class AccLinkUserSerializer(serializers.Serializer):

    openid = serializers.CharField()
    accid = serializers.IntegerField()
    nickname = serializers.CharField()
    sex = serializers.CharField()
    province = serializers.CharField()
    country = serializers.CharField()
    city = serializers.CharField()
    tags = serializers.SerializerMethodField()
    subscribe_time = serializers.SerializerMethodField()
    subscribe_scene = serializers.CharField()
    memo = serializers.CharField()
    headimgurl = serializers.CharField()

    def get_tags(self,obj):
        return AccTagModelSerializer(AccTag.objects.filter(id__in=json.loads(obj.tags)).order_by('-createtime'),many=True).data

    def get_subscribe_time(self,obj):
        return UtilTime().timestamp_to_string(obj.subscribe_time)

class AccFollowModelSerializer(serializers.ModelSerializer):

    lists = serializers.SerializerMethodField()
    acc = serializers.SerializerMethodField()

    def get_acc(self,obj):
        try:
            return AccSerializer(Acc.objects.get(accid=obj.accid), many=False).data
        except AccQrcode.DoesNotExist:
            return {}

    def get_lists(self,obj):
        return AccQrcodeListModelSerializer(AccQrcodeList.objects.filter(id__in=json.loads(obj.listids)).order_by('sort'),many=True).data

    class Meta:
        model = AccFollow
        fields = '__all__'

class AccReplyModelSerializer(serializers.ModelSerializer):

    lists = serializers.SerializerMethodField()
    acc = serializers.SerializerMethodField()

    def get_acc(self,obj):
        try:
            return AccSerializer(Acc.objects.get(accid=obj.accid), many=False).data
        except AccQrcode.DoesNotExist:
            return {}

    def get_lists(self,obj):
        return AccQrcodeListModelSerializer(AccQrcodeList.objects.filter(id__in=json.loads(obj.listids)).order_by('sort'),many=True).data

    class Meta:
        model = AccReply
        fields = '__all__'


class AccQrcodeModelSerializer(serializers.ModelSerializer):

    tags = serializers.SerializerMethodField()
    lists = serializers.SerializerMethodField()
    acc = serializers.SerializerMethodField()
    createtime = serializers.SerializerMethodField()
    endtime = serializers.SerializerMethodField()

    def get_createtime(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime,format_v="%Y-%m-%d")

    def get_endtime(self,obj):
        if obj.endtime:
            return UtilTime().timestamp_to_string(obj.endtime, format_v="%Y-%m-%d")
        else:
            return ""

    def get_acc(self,obj):
        try:
            return AccSerializer(Acc.objects.get(accid=obj.accid), many=False).data
        except AccQrcode.DoesNotExist:
            return {}

    def get_tags(self,obj):
        return AccTagModelSerializer(AccTag.objects.filter(id__in=json.loads(obj.tags)).order_by('-createtime'),many=True).data

    def get_lists(self,obj):
        return AccQrcodeListModelSerializer(AccQrcodeList.objects.filter(id__in=json.loads(obj.listids)).order_by('sort'),many=True).data


    class Meta:
        model = AccQrcode
        fields = ('id','name','accid','tot_count','createtime','acc','new_count','follow_count','type','endtime','qr_type','send_type','url','tags','lists',)

class AccQrcodeListModelSerializer(serializers.ModelSerializer):

    imagetextlist=serializers.SerializerMethodField()

    local_url = serializers.SerializerMethodField()

    def get_local_url(self,obj):

        if obj.media_id:
            return "{}{}".format(ServerUrl,Meterial.objects.get(media_id=obj.media_id).local_url)
        else:
            return ""

    def get_imagetextlist(self,obj):
        return AccQrcodeImageTextListModelSerializer(AccQrcodeImageTextList.objects.filter(id__in=json.loads(obj.iamgetextids)).order_by('sort'),
                                            many=True).data

    class Meta:
        model = AccQrcodeList
        fields = '__all__'

class AccQrcodeImageTextListModelSerializer(serializers.ModelSerializer):

    local_url = serializers.SerializerMethodField()

    def get_local_url(self,obj):

        if obj.media_id:
            return "{}{}".format(ServerUrl,Meterial.objects.get(media_id=obj.media_id).local_url)
        else:
            return ""

    class Meta:
        model = AccQrcodeImageTextList
        fields = '__all__'

class AccTagModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccTag
        fields = '__all__'
