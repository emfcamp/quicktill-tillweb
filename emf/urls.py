from django.urls import path, include
from emf.views import *

urls = [
    path('', frontpage, name="frontpage"),
    path('locations.json', locations_json, name="locations-json"),
    path('location/<location>.json', location_json,
         name="location-json"),
    path('stock.json', stock_json, name="stock-json"),
    path('progress.json', progress_json, name="progress-json"),
    path('sessions.json', sessions_json, name="sessions-json"),
    path('refusals/', refusals, name="refusals"),
    path('display/', display, name="display"),
    path('display/info.json', display_info, name="display-info"),
    path('display/<page>/', display, name="display-page"),
    path('display/<page>/info.json', display_page_info,
         name="display-page-info"),
]
