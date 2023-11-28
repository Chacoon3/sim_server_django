from typing import Callable

class InMemoryCache:

    def __init__(self):
        self.__cache = {}

    def get_or_query(self, key, callable: Callable):
        if self.__cache.get(key) is None:
            self.__cache[key] = callable()
        return self.__cache[key]

    def delete(self, key):
        self.__cache.pop(key, None)

    def clear(self):
        self.__cache.clear()

    def __str__(self):
        return str(self.__cache)

class BMGT435_DB_Router:

    __main_db = 'default'
    __session_db = 'session_db'

    def db_for_read(self, model, **hints):
        raise   NotImplementedError('db_for_read not implemented')
    
    def db_for_write(self, model, **hints):
        raise   NotImplementedError('db_for_read not implemented')

    def allow_relation(self, obj1, obj2, **hints):
        return True
    
    def allow_migration(self, db, app_label, model_name=None, **hints):
        return True    
