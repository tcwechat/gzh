
import json
from rest_framework import serializers
from app.wechat.models import Acc,AccTag,AccQrcode,AccQrcodeList,AccQrcodeImageTextList
from lib.utils.mytime import UtilTime

class AccSerializer(serializers.Serializer):

    accid = serializers.IntegerField()
    nick_name = serializers.CharField()
    head_img = serializers.CharField()
    createtime = serializers.IntegerField()

class AccQrcodeModelSerializer(serializers.Serializer):

    tags = serializers.SerializerMethodField()
    lists = serializers.SerializerMethodField()

    def get_tags(self,obj):
        return AccTagModelSerializer(AccTag.objects.filter(id__in=json.loads(obj.tags).order_by('-createtime')),many=True).data

    def get_lists(self,obj):
        return AccQrcodeListModelSerializer(AccQrcodeList.objects.filter(id__in=json.loads(obj.listids)),many=True).data


    class Meta:
        model = AccQrcode
        fields = ('name','accid','tot_count','new_count','follow_count','type','endtime','qr_type','send_type','url',)

class AccQrcodeListModelSerializer(serializers.ModelSerializer):

    imagetextlist=serializers.SerializerMethodField()

    def get_imagetextlist(self,obj):
        return AccQrcodeImageTextListModelSerializer(AccQrcodeImageTextList.objects.filter(id__in=json.loads(obj.iamgetextids)),
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
