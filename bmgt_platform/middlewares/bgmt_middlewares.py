
def CORSMiddleware(get_response):
    """
    this allows the frontend to access the backend otherwise the CORS requests get blocked
    """
    
    def middleware(request):

        response = get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Credentials"] = "true"

        return response
    
    return middleware