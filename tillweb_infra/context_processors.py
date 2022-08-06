from django.conf import settings


def pubname_setting(request):
    return {'TILLWEB_PUBNAME': settings.TILLWEB_PUBNAME}


def emfsso_user(request):
    return {'EMFSSO_USER': request.session.get('emfsso-user', False)}
