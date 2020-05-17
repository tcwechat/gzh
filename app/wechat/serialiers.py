
import json
from rest_framework import serializers
from app.wechat.models import Acc,AccTag,AccQrcode,AccQrcodeList,AccQrcodeImageTextList
from lib.utils.mytime import UtilTime

class AccSerializer(serializers.Serializer):

    accid = serializers.IntegerField()
    nick_name = serializers.CharField()
    head_img = serializers.CharField()
    createtime = serializers.IntegerField()

class AccQrcodeModelSerializer(serializers.ModelSerializer):

    tags = serializers.SerializerMethodField()
    lists = serializers.SerializerMethodField()
    acc = serializers.SerializerMethodField()
    createtime = serializers.SerializerMethodField()

    def get_createtime(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime,format_v="%Y-%m-%d")

    def get_acc(self,obj):
        try:
            return AccSerializer(Acc.objects.get(id=obj.accid), many=False).data
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

    def get_imagetextlist(self,obj):
        return AccQrcodeImageTextListModelSerializer(AccQrcodeImageTextList.objects.filter(id__in=json.loads(obj.iamgetextids)).order_by('sort'),
                                            many=True).data

    class Meta:
        model = AccQrcodeList
        fields = '__all__'

class AccQrcodeImageTextListModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccQrcodeImageTextList
        fields = '__all__'

class AccTagModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccTag
        fields = '__all__'
