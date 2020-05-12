
from project.config_include.common import ServerUrl
from rest_framework import viewsets
from rest_framework.decorators import list_route

from lib.core.decorator.response import Core_connector
from lib.utils.exceptions import PubErrorCustom

from app.user.serialiers import UsersModelSerializer,RoleModelSerializer
from app.user.models import Users,Role

class UserAPIView(viewsets.ViewSet):

    @list_route(methods=['POST'])
    @Core_connector(isTicket=True)
    def userinfo(self,request, *args, **kwargs):

        return {"data": {
            "userid": request.user.get("userid"),
            "loginname": request.user.get("uuid"),
            "username": request.user.get("name"),
            "rolecode":request.user.get("rolecode"),
            "avatar": ServerUrl+'/static/images/pic.jpg',
            "menu": []
        }}