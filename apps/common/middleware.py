class CleanCORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Origin 헤더 정리
        if "HTTP_ORIGIN" in request.META:
            # 첫 번째 Origin만 유지
            origins = request.META["HTTP_ORIGIN"].split(",")
            request.META["HTTP_ORIGIN"] = origins[0].strip()

        response = self.get_response(request)
        return response
