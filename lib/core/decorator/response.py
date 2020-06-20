import time,jsonfrom functools import wrapsfrom django.db import transactionfrom django.core.serializers.json import DjangoJSONEncoderfrom lib.core.http.response import HttpResponsefrom lib.core.paginator import Paginationfrom lib.utils.log import loggerfrom lib.utils.exceptions import PubErrorCustom,InnerErrorCustomfrom lib.utils.passwd import decrypt,encryptfrom lib.utils.db import RedisTokenHandlerfrom include import error as errorlistfrom lib.utils.wechat.ticket import WechatRequestValidclass Core_connector:    def __init__(self,**kwargs):        #是否加数据库事务        self.isTransaction = kwargs.get('isTransaction',False)        #是否分页        self.isPagination = kwargs.get('isPagination',False)        #是否加密        self.isPasswd = kwargs.get('isPasswd', False)        #是否校验ticket        self.isTicket = kwargs.get('isTicket', False)        #是否自定义返回        self.isReturn = kwargs.get("isReturn",False)        #是否校验请求合法性(微信开放平台用)        self.isRVliad = kwargs.get("isRVliad",False)        self.serializer_class = kwargs.get("serializer_class",False)        self.model_class = kwargs.get("model_class",False)    #前置处理    def __request_validate(self,request,**kwargs):        if self.isRVliad:            WechatRequestValid().run(                request.query_params['timestamp'],                request.query_params['nonce'],                request.query_params['signature']            )        #校验凭证并获取用户数据        if self.isTicket:            ticket = request.META.get('HTTP_AUTHORIZATION')            if not ticket:                raise InnerErrorCustom(code="20001",msg="ticket不存在!")            result = RedisTokenHandler(key=ticket).get()            if not result:                raise InnerErrorCustom(code="20002",msg="ticket已失效!")            if result.get("status") == '1':                raise PubErrorCustom("账户已到期!")            elif result.get("status") == '2':                raise PubErrorCustom("账户已冻结!")            request.user = result            request.ticket = ticket        if self.isPasswd:            if request.method == 'GET':                if 'data' not in request.query_params:                    raise PubErrorCustom("拒绝访问!!")                if request.query_params.get('data') and len(                    request.query_params.get('data')) and request.query_params.get('data') != '{}':                    request.query_params_format = json.loads(decrypt(request.query_params.get('data')))                else:                    request.query_params_format = {}            if request.method in ['POST','PUT','DELETE']:                if 'data' not in request.data:                    raise PubErrorCustom("拒绝访问!!")                if request.data.get('data') and len(request.data.get('data')):                    request.data_format = json.loads(decrypt(request.data.get('data')))                else:                    request.data_format = {}        else:            try:                print(request.data)                request.data_format = request.data.get("data") if 'data' in request.data else {}                if isinstance(request.data_format,str):                    request.data_format = json.loads(request.data_format)                request.query_params_format = json.loads(request.query_params.get("data")) if 'data' in request.query_params else {}                if self.isPagination:                    page = int(request.query_params_format.get("page",1))                    page_size = int(request.query_params_format.get("size",10))                    request.page_start = page_size * page - page_size                    request.page_end = page_size * page                    request.offset = page_size * page - page_size                    request.count = page_size            except Exception as e:                print(str(e))        if self.serializer_class:            # pk = kwargs.get('pk')            instance = None            if request.data_format.get("updKey"):                try:                    instance = self.model_class.objects.get(**{                        request.data_format.get("updKey"):request.data_format.get("key")                    })                except TypeError:                    raise PubErrorCustom('serializer_class类型错误')                except Exception:                    raise PubErrorCustom('未找到')            serializer = self.serializer_class(data=request.data_format, instance=instance)            if not serializer.is_valid():                errors = [key + ':' + value[0] for key, value in serializer.errors.items() if isinstance(value, list)]                if errors:                    error = errors[0]                    error = error.lstrip(':').split(':')                    try:                        error = "{}:{}".format( getattr( errorlist,error[0]) , error[1])                    except AttributeError as e:                        error = error[1]                else:                    for key, value in serializer.errors.items():                        if isinstance(value, dict):                            key, value = value.popitem()                            error = key + ':' + value[0]                            break                raise PubErrorCustom(error)            kwargs.setdefault('serializer',serializer)            kwargs.setdefault('instance', instance)        return kwargs    def __run(self,func,outside_self,request,*args, **kwargs):        if self.isTransaction:            with transaction.atomic():                res = func(outside_self, request, *args, **kwargs)        else:            res = func(outside_self, request, *args, **kwargs)        if self.isReturn:            logger.info("返回报文:{}".format(res))            return res        else:            # if res and 'data' in res and \            #     ((self.isPagination and isinstance(res['data'], list)) or (            #         self.isPagination and isinstance(res['data'], dict) and 'data' in res['data'])):            #     if 'header' in res:            #         header = res['header']            #         res = Pagination().get_paginated(data=res['data'], request=request)            #         res['header'] = {**res['header'], **header}            #     else:            #         res = Pagination().get_paginated(data=res['data'], request=request)            if not isinstance(res, dict):                res = {'data': None, 'msg': None, 'header': None}            if 'data' not in res:                res['data'] = None            if 'msg' not in res:                res['msg'] = {}            if 'count' not in res:                res['count'] = 0            if 'header' not in res:                res['header'] = None            if self.isPasswd:                res['data'] = encrypt(json.dumps(res['data'], cls=DjangoJSONEncoder))            else:                res['data'] = res['data']            logger.info("返回报文:{}".format(res['data']))            return HttpResponse(data=res['data'], headers=res['header'], msg=res['msg'],count=res['count'])    #后置处理    def __response__validate(self,outside_self,func,response,request):        # if self.isCache:        #     for cash_save_item in request.cache_save:        #         RedisCaCheHandler(**request.cash_save_item).run()        logger.info('[%s : %s]Training complete in %lf real seconds' % (outside_self.__class__.__name__, getattr(func, '__name__'), self.end - self.start))        return response    def __call__(self,func):        @wraps(func)        def wrapper(outside_self,request,*args, **kwargs):            try:                self.start = time.time()                kwargs=self.__request_validate(request,**kwargs)                response=self.__run(func,outside_self,request,*args, **kwargs)                self.end=time.time()                return self.__response__validate(outside_self,func,response,request)            except PubErrorCustom as e:                logger.error('[%s : %s  ] : [%s]'%(outside_self.__class__.__name__, getattr(func, '__name__'),e.msg))                return HttpResponse(success=False, msg=e.msg, data=None)            except InnerErrorCustom as e:                logger.error('[%s : %s  ] : [%s]'%(outside_self.__class__.__name__, getattr(func, '__name__'),e.msg))                return HttpResponse(success=False, msg=e.msg, rescode=e.code, data=None)            except Exception as e:                logger.error('[%s : %s  ] : [%s]'%(outside_self.__class__.__name__, getattr(func, '__name__'),str(e)))                return HttpResponse(success=False, msg=str(e), data=None)        return wrapper