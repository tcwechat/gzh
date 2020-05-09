
from rest_framework import viewsets
from rest_framework.decorators import list_route

from lib.core.decorator.response import Core_connector
from lib.utils.exceptions import PubErrorCustom
from lib.utils.db import RedisTokenHandler
from lib.utils.string_extension import get_token
from lib.utils.http_request import send_request_other

from app.user.models import Users
from app.user.serialiers import UsersSerializers


class SsoAPIView(viewsets.ViewSet):
    pass