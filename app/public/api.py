
import uuid,os
from rest_framework import viewsets
from rest_framework.decorators import list_route
from project.config_include.common import ServerUrl
from lib.core.decorator.response import Core_connector
from lib.utils.exceptions import PubErrorCustom
from project.settings import IMAGE_PATH

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