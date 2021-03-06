from django.conf import settings
from django.conf.urls import url
from django.core.paginator import Paginator
from tastypie.resources import ModelResource
from tastypie.throttle import CacheThrottle
from tastypie.utils import trailing_slash
from borme.documents import es_search_paginator
from borme.models import Company, Person
# from borme.utils.postgres import search_fts
from .serializers import LibreBormeJSONSerializer


# FIXME: fullname
class CompanyResource(ModelResource):
    class Meta:
        excludes = ['document', 'nif']
        detail_allowed_methods = ['get']
        list_allowed_methods = []
        max_limit = 100
        queryset = Company.objects.all()
        resource_name = 'empresa'
        serializer = LibreBormeJSONSerializer(formats=['json'])
        # 60 requests per hour ~= 1 request per minute
        throttle = CacheThrottle(throttle_at=60, timeframe=3600)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search_company"),
        ]

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        objects = []
        query = request.GET.get('q', '')

        if len(query) > 3:
            # If you want to use postgres FTS, change to:
            #
            # sqs = search_fts(query, model=Company)
            # paginator = Paginator(sqs, 20)
            # ...
            #    for result in page.object_list:

            sqs = es_search_paginator('company_document', query)
            paginator = Paginator(sqs, 20)

            try:
                page = paginator.page(int(request.GET.get('page', 1)))

                slugs = list(map(lambda x: x['_source']['slug'], page))
                object_list = Company.objects.filter(slug__in=slugs)
                for result in object_list:
                    bundle = self.build_bundle(obj=result, request=request)
                    bundle = self.search_dehydrate(bundle)
                    objects.append(bundle)
            except:
                pass

        object_list = {
            'objects': objects,
        }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)

    # HACK: Based on full_dehydrate
    def search_dehydrate(self, bundle, for_list=False):
        use_in = ['all', 'list' if for_list else 'detail']

        for field_name, field_object in self.fields.items():
            if field_name not in ('slug', 'name', 'resource_uri'):
                continue

            field_use_in = getattr(field_object, 'use_in', 'all')
            if callable(field_use_in):
                if not field_use_in(bundle):
                    continue
            else:
                if field_use_in not in use_in:
                    continue

            if getattr(field_object, 'dehydrated_type', None) == 'related':
                field_object.api_name = self._meta.api_name
                field_object.resource_name = self._meta.resource_name

            bundle.data[field_name] = field_object.dehydrate(bundle, for_list=for_list)

            method = getattr(self, "dehydrate_%s" % field_name, None)

            if method:
                bundle.data[field_name] = method(bundle)

        bundle = self.dehydrate(bundle)
        return bundle


class PersonResource(ModelResource):
    class Meta:
        excludes = ['document']
        detail_allowed_methods = ['get']
        list_allowed_methods = []
        max_limit = 100
        queryset = Person.objects.all()
        resource_name = 'persona'
        serializer = LibreBormeJSONSerializer(formats=['json'])
        throttle = CacheThrottle(throttle_at=60, timeframe=3600)

    def dehydrate_name(self, bundle):
        return bundle.data['name'].title()

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search_person"),
        ]

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        objects = []
        query = request.GET.get('q', '')

        if len(query) > 3:
            # If you want to use postgres FTS, change to:
            #
            # sqs = search_fts(query, model=Person)
            # paginator = Paginator(sqs, 20)
            # ...
            #    for result in page.object_list:

            sqs = es_search_paginator('person_document', query)
            paginator = Paginator(sqs, 20)

            try:
                page = paginator.page(int(request.GET.get('page', 1)))

                slugs = list(map(lambda x: x['_source']['slug'], page))
                object_list = Person.objects.filter(slug__in=slugs)
                for result in object_list:
                    bundle = self.build_bundle(obj=result, request=request)
                    bundle = self.search_dehydrate(bundle)
                    objects.append(bundle)
            except:
                pass

        object_list = {
            'objects': objects,
        }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)

    # HACK: Based on full_dehydrate
    def search_dehydrate(self, bundle, for_list=False):
        use_in = ['all', 'list' if for_list else 'detail']

        for field_name, field_object in self.fields.items():
            if field_name not in ('slug', 'name', 'resource_uri'):
                continue

            field_use_in = getattr(field_object, 'use_in', 'all')
            if callable(field_use_in):
                if not field_use_in(bundle):
                    continue
            else:
                if field_use_in not in use_in:
                    continue

            if getattr(field_object, 'dehydrated_type', None) == 'related':
                field_object.api_name = self._meta.api_name
                field_object.resource_name = self._meta.resource_name

            bundle.data[field_name] = field_object.dehydrate(bundle, for_list=for_list)

            method = getattr(self, "dehydrate_%s" % field_name, None)

            if method:
                bundle.data[field_name] = method(bundle)

        bundle = self.dehydrate(bundle)
        return bundle
