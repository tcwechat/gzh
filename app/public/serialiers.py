
from rest_framework import serializers
from project.config_include.common import ServerUrl

class MeterialSerializer(serializers.Serializer):

    local_url = serializers.SerializerMethodField()
    title = serializers.CharField()
    introduction = serializers.CharField()
    media_id = serializers.CharField()
    url = serializers.CharField()

    def get_local_url(self,obj):

        return "{}{}".format(ServerUrl,obj.local_url)

