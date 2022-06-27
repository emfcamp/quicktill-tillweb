from django.conf import settings
from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from tillweb_infra import views

admin.autodiscover()
admin.site.site_header = "Till administration"

import photologue.urls
import quicktill.tillweb.urls
import emf.urls

urlpatterns = [
    path('accounts/', include([
        path('login/', auth_views.LoginView.as_view(
            extra_context={'EMFSSO_ENABLED': settings.EMFSSO_ENABLED}),
             name="login-page"),
        path('logout/', auth_views.LogoutView.as_view(), name="logout-page"),
        path('profile/', views.userprofile, name="user-profile-page"),
        path('change-password/', views.pwchange, name="password-change-page"),
        path('users/', views.users, name="userlist"),
        path('users/<int:userid>/', views.userdetail, name="userdetail"),
        path('oauth2/login/', views.emfsso_login, name="emfsso-login"),
        path('oauth2/callback/', views.emfsso_callback, name="emfsso-callback"),
    ])),
    path('admin/', admin.site.urls),
    path('detail/', include(quicktill.tillweb.urls.tillurls),
         {"pubname": "detail"}),
    path('photos/', include(photologue.urls, namespace='photologue')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns.append(path('', include(emf.urls.urls)))
