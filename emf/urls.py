from django.urls import path
from emf import views
from emf import api

urls = [
    path('', views.frontpage, name="frontpage"),
    path('prices/', views.pricelist, name="pricelist"),
    path('refusals/', views.refusals, name="refusals"),
    path('display/', views.display, name="display"),
    path('display/info.json', views.display_info, name="display-info"),
    path('display/<page>/', views.display, name="display-page"),
    path('display/<page>/info.json', views.display_page_info,
         name="display-page-info"),

    path('jontyfacts/', views.jontyfacts, name="jontyfacts"),

    path('api/sessions.json', views.api_sessions, name="api-sessions"),
    path('api/progress.json', views.api_progress, name="api-progress"),
    path('api/departments.json', api.departments, name="api-departments"),
    path('api/on-tap.json', api.api_on_tap, name="api-on-tap"),
    path('api/cybar.json', api.cybar, name="api-cybar"),
    path('api/stocktypes.json', api.stock, name="api-stocktypes"),
    path('api/shop.json', api.shop, name="api-shop"),
    path('api/department/<int:dept_id>.json', api.dept, name="api-dept"),
    path('api/stocktype/<int:stocktype_id>.json', api.stocktype,
         name="api-stocktype"),
]
