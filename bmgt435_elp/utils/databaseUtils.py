import bmgt435_platform.bmgtAnalyticsModel as bmgtAnalyticsModel

class BMGT435_DB_Router:


    def db_for_read(self, model, **hints):
        raise NotImplementedError("db_for_read method not implemented")
    
    def db_for_write(self, model, **hints):
        raise NotImplementedError("db_for_read method not implemented")

    def allow_relation(self, obj1, obj2, **hints):
        return True
    
    def allow_migration(self, db, app_label, model_name=None, **hints):
        return True    
