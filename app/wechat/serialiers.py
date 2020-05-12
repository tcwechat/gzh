
import json
from rest_framework import serializers
from app.wechat.models import Acc,AccTag
from lib.utils.mytime import UtilTime

class AccSerializer(serializers.Serializer):

    accid = serializers.IntegerField()
    nick_name = serializers.CharField()
    head_img = serializers.CharField()
    createtime = serializers.IntegerField()


class AccTagModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccTag
        fields = '__all__'
