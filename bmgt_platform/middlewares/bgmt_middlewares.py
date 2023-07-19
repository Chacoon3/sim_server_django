
def CORSMiddleware(get_response):
    """
    this enables the CORS policy so that frontend can access the backend
    """
    
    def middleware(request):

        response = get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Credentials"] = "true"

        return response
    
    return middleware