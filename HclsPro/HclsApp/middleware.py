from HclsWebApi.authentication import get_request_actor


class JWTActorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_actor = get_request_actor(request)
        return self.get_response(request)
