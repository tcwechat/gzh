
from project.config_include.common import ServerUrl
from rest_framework import viewsets
from rest_framework.decorators import list_route

from lib.core.decorator.response import Core_connector
from lib.utils.exceptions import PubErrorCustom

from app.user.serialiers import UsersModelSerializer,RoleModelSerializer
from app.user.models import Users,Role

class UserAPIView(viewsets.ViewSet):

    pass