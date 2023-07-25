from django.core import serializers
from django.core.paginator import Paginator, Page
# from django.db.models.query import QuerySet
# from ..bmgt_models import *

import json


class Query:

    __DEF_PAGE_SIZE = 10

    @staticmethod
    def to_paginator_response(paginator: Paginator, page: int) -> str:
        """
        convert a query set acquired by pagination to a json string
        """

        return json.dumps({
            "page": page,
            "page_size": paginator.per_page,
            "total_page": paginator.num_pages,
            "total_count": paginator.count,
            "has_next": paginator.page(page).has_next(),
            "has_previous": paginator.page(page).has_previous(),
            "data": json.loads(serializers.serialize("json", paginator.page(page).object_list)),
        })

    @staticmethod
    def exists(db_model, **kwargs) -> bool:
        return db_model.objects.filter(**kwargs).exists()

    @staticmethod
    def fetch_one(db_model, **kwargs) -> str:
        return serializers.serialize("json", [db_model.objects.get(**kwargs)])

    @staticmethod
    def delete_one(db_model, **kwargs) -> bool:
        db_model.objects.get(**kwargs).delete()
        return True

    @staticmethod
    def create_or_update_one(db_model, **kwargs) -> str | None:
        obj, success = db_model.objects.update_or_create(kwargs)
        if success:
            return serializers.serialize("json", [obj])
        else:
            return None

    @staticmethod
    def fetch_page(db_model, **kwargs) -> str:

        page_index = kwargs["page_index"]
        page_size = kwargs.get("page_size") or Query.__DEF_PAGE_SIZE
        order_by = kwargs.get("order_by") or "id"
        asc = kwargs.get("asc") or True

        pager = Paginator(
            db_model.objects.all().order_by(order_by if asc else '-'+order_by),
            page_size
        )

        if page_index > pager.num_pages:
            raise Exception("page index out of range")

        return Query.to_paginator_response(pager, page_index)

    @staticmethod
    def fetch_all(db_model,  **kwargs) -> str:

        if kwargs:
            querySet = db_model.objects.filter(kwargs)
        else:
            querySet = db_model.objects.all()

        return serializers.serialize("json", querySet)

    @staticmethod
    def create_all(db_model, iterator_objs) -> str:
        querySet = db_model.objects.bulk_create(
            [data.object for data in iterator_objs])
        return serializers.serialize("json", querySet)

    @staticmethod
    def update_all(db_model, iterator_objs) -> str:

        querySet = db_model.objects.bulk_update(
            [data.object for data in iterator_objs])
        return serializers.serialize("json", querySet)


    @staticmethod
    def delete_all(db_model, **kwargs) -> bool:
        db_model.objects.filter(kwargs).delete()
        return True
