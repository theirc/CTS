from django.http import HttpResponse


def health_view(request):
    return HttpResponse("I am okay.", content_type="text/plain")
