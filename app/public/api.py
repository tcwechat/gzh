
import uuid,os
from rest_framework import viewsets
from rest_framework.decorators import list_route
from project.config_include.common import ServerUrl
from lib.core.decorator.response import Core_connector
from lib.utils.exceptions import PubErrorCustom
from project.settings import IMAGE_PATH

from lib.utils.wechat.material import WechatMaterial
from app.public.models import Meterial

class PublicAPIView(viewsets.ViewSet):

    @list_route(methods=['POST','OPTIONS'])
    @Core_connector()
    def file(self,request, *args, **kwargs):

        file_obj = request.FILES.get('filename')
        if file_obj:

            new_file = "{}_{}".format(uuid.uuid4().hex,file_obj.name)

            file_path =os.path.join(IMAGE_PATH, new_file)
            with open(file_path,'wb+') as f:
                for chunk in file_obj.chunks():
                    f.write(chunk)

            return {"data":{"path":"{}/static/images/{}".format(ServerUrl,new_file)}}

        else:
            raise PubErrorCustom("文件上传失败!")

    @list_route(methods=['POST', 'OPTIONS'])
    @Core_connector()
    def wechat_file(self, request, *args, **kwargs):

        #chunk for chunk in request.FILES.get('filename').chunks()
        media_id,url = WechatMaterial(accid=request.data_format.get("accid","")).create_forever(
            meterialObj=request.FILES.get('filename'),
            type=request.data_format.get("type",""),
            title=request.data_format.get("title",""),
            introduction=request.data_format.get("introduction","")
        )
        print(media_id,url)
        Meterial.objects.create(** dict(
            type = request.data_format.get("type",""),
            title = request.data_format.get("title",""),
            introduction=request.data_format.get("introduction", ""),
            media_id = media_id,
            url = url
        ))