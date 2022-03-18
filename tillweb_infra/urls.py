from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from tillweb_infra import views

admin.autodiscover()
admin.site.site_header = "Till administration"

import quicktill.tillweb.urls

urlpatterns = [
    path('accounts/', include([
        path('login/', auth_views.LoginView.as_view(), name="login-page"),
        path('logout/', auth_views.LogoutView.as_view(), name="logout-page"),
        path('profile/', views.userprofile, name="user-profile-page"),
        path('change-password/', views.pwchange, name="password-change-page"),
        path('users/', views.users, name="userlist"),
        path('users/<int:userid>/', views.userdetail, name="userdetail"),
    ])),
    path('admin/', admin.site.urls),
    path('detail/', include(quicktill.tillweb.urls.tillurls),
         {"pubname": "detail"}),
]

from .emfurls import emfurls
urlpatterns += emfurls
