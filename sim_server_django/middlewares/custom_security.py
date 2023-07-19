from django.middleware.security import SecurityMiddleware

class CustomSecurityMiddleware(SecurityMiddleware):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    
    