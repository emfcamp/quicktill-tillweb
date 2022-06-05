from django.urls import path, include
from emf.views import *
from emf import api

urls = [
    path('', frontpage, name="frontpage"),
    path('prices/', pricelist, name="pricelist"),
    path('refusals/', refusals, name="refusals"),
    path('display/', display, name="display"),
    path('display/info.json', display_info, name="display-info"),
    path('display/<page>/', display, name="display-page"),
    path('display/<page>/info.json', display_page_info,
         name="display-page-info"),

    path('jontyfacts/', jontyfacts, name="jontyfacts"),

    path('api/sessions.json', api_sessions, name="api-sessions"),
    path('api/progress.json', api_progress, name="api-progress"),
    path('api/departments.json', api.departments, name="api-departments"),
    path('api/on-tap.json', api.api_on_tap, name="api-on-tap"),
    path('api/cybar.json', api.cybar, name="api-cybar"),
    path('api/stocktypes.json', api.stock, name="api-stocktypes"),
    path('api/shop.json', api.shop, name="api-shop"),
    path('api/department/<int:dept_id>.json', api.dept, name="api-dept"),
    path('api/stocktype/<int:stocktype_id>.json', api.stocktype,
         name="api-stocktype"),
]
