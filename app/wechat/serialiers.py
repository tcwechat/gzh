
import json
from rest_framework import serializers
from app.wechat.models import Acc
from lib.utils.mytime import UtilTime

class AccSerializer(serializers.Serializer):

    accid = serializers.IntegerField()
    nick_name = serializers.CharField()
    head_img = serializers.CharField()
    createtime = serializers.IntegerField()