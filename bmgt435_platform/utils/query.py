from django.core.paginator import Paginator, Page
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned



class Query:

    __DEF_PAGE_SIZE = 10


    @staticmethod
    def __query_error_handler(func):

        def wrapper(db_model, **kwargs):
            try:
                return func(db_model, **kwargs)

            except ObjectDoesNotExist:
                return None
            except Exception as e:
                raise
            
        return wrapper

    @__query_error_handler
    @staticmethod
    def exists(db_model, **kwargs) -> bool:
        return db_model.objects.filter(**kwargs).exists()

    @__query_error_handler
    @staticmethod
    def fetch_one(db_model, **kwargs) -> object:
        return db_model.objects.get(**kwargs)

    @__query_error_handler
    @staticmethod
    def delete_one(db_model, **kwargs) -> bool:
        db_model.objects.get(**kwargs).delete()
        return True

    @__query_error_handler
    @staticmethod
    def create_or_update_one(db_model, **kwargs) -> object:
        obj, success = db_model.objects.update_or_create(kwargs)
        if success:
            return obj
        else:
            return None

    @__query_error_handler
    @staticmethod
    def fetch_page(db_model, **kwargs) -> Page:

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

        return pager.page(page_index)

    @__query_error_handler
    @staticmethod
    def fetch_all(db_model,  **kwargs) -> QuerySet:

        if kwargs:
            querySet = db_model.objects.filter(kwargs)
        else:
            querySet = db_model.objects.all()

        return querySet

    @__query_error_handler
    @staticmethod
    def create_all(db_model, iterator_objs) -> QuerySet:
        querySet = db_model.objects.bulk_create(
            [data.object for data in iterator_objs])
        return querySet

    @__query_error_handler
    @staticmethod
    def update_all(db_model, iterator_objs) -> QuerySet:

        querySet = db_model.objects.bulk_update(
            [data.object for data in iterator_objs])
        return querySet

    @__query_error_handler
    @staticmethod
    def delete_all(db_model, **kwargs) -> bool:
        db_model.objects.filter(kwargs).delete()
        return True
