
import uuid,os
from rest_framework import viewsets
from rest_framework.decorators import list_route
from project.config_include.common import ServerUrl
from lib.core.decorator.response import Core_connector
from lib.utils.exceptions import PubErrorCustom
from project.settings import IMAGE_PATH,BASE_DIR

from lib.utils.wechat.material import WechatMaterial
from app.public.models import Meterial
from app.public.serialiers import MeterialSerializer

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
    @Core_connector(isTransaction=True)
    def meterial(self, request, *args, **kwargs):

        file_obj = request.FILES.get('filename')
        if file_obj:

            new_file = "{}_{}".format(uuid.uuid4().hex, file_obj.name)

            file_path = os.path.join(IMAGE_PATH, new_file)

            file_strem = file_obj.read()

            saveFileUrl = "/static/images/{}".format(new_file)
            fileUrl = "{}/static/images/{}".format(ServerUrl, new_file)

            media_id, url = WechatMaterial(accid=request.data_format.get("accid", "")).create_forever(
                meterialObj={"file":file_strem,"filename":new_file},
                type=request.data_format.get("type", ""),
                title=request.data_format.get("title", ""),
                introduction=request.data_format.get("introduction", "")
            )

            with open(file_path, 'wb+') as f:
                f.write(file_strem)

            Meterial.objects.create(**dict(
                type=request.data_format.get("type", ""),
                title=request.data_format.get("title", ""),
                accid=request.data_format.get("accid",0),
                introduction=request.data_format.get("introduction", ""),
                media_id=media_id,
                url=url,
                local_url = saveFileUrl
            ))
            return {"data": {"path":fileUrl,"media_id":media_id}}

        else:
            raise PubErrorCustom("文件上传失败!")

    @list_route(methods=['GET'])
    @Core_connector(isPagination=True)
    def meterial_get(self, request, *args, **kwargs):

        mQuery = Meterial.objects.filter(accid=request.query_params_format.get("accid",0),type=request.query_params_format.get("type",None)).order_by('-createtime')

        count = mQuery.count()

        return {"data":MeterialSerializer(mQuery[request.page_start:request.page_end],many=True).data,"count":count}


    @list_route(methods=['DELETE'])
    @Core_connector(isTransaction=True)
    def meterial_delete(self, request, *args, **kwargs):

        try:
            obj = Meterial.objects.get(media_id=request.data_format.get("media_id",0))
        except Meterial.DoesNotExist:
            raise PubErrorCustom("此素材不存在!")

        WechatMaterial(accid=obj.accid).delete_forever(obj.media_id)

        os.remove(BASE_DIR+obj.local_url)
        obj.delete()

        return None