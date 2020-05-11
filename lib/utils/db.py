
import json
from   django_redis  import   get_redis_connection
from lib.utils.exceptions import PubErrorCustom
from lib.utils.mytime import UtilTime

class RedisHandler(object):
    def __init__(self,**kwargs):
        self.redis_client = get_redis_connection(kwargs.get("db") if kwargs.get("db") else 'default')
        self.key = str(kwargs.get("key"))


class RedisTicketHandler(RedisHandler):

    def __init__(self):
        super().__init__(db="wechatTicket",key="ComponentVerifyTicket")

    def set(self,value):
        self.redis_client.set(self.key, value)

    def get(self):
        s=self.redis_client.get(self.key)
        print("{ticket:{}".format(s))
        return s

class RedisAccessTokenHandler(RedisHandler):
    def __init__(self):
        super().__init__(db="wechatTicket",key="component_access_token")

    def set(self,value,expire):
        self.redis_client.set(self.key, value)
        self.redis_client.set(self.key,expire)

    def get(self):
        return self.redis_client.get(self.key)

class RedisTokenHandler(RedisHandler):

    def __init__(self,**kwargs):
        kwargs.setdefault('db', 'token')
        super().__init__(**kwargs)

    def set(self,value):
        self.redis_client.set(self.key, json.dumps(value))

    def get(self):
        res = self.redis_client.get(self.key)
        return json.loads(res) if res else res