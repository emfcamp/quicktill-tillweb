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
    path('display/on-tap.html', display_on_tap, name="display-on-tap"),
    path('display/cans-and-bottles.html', display_cans_and_bottles,
         name="display-cans-and-bottles"),
    path('display/wines-and-spirits.html', display_wines_and_spirits,
         name="display-wines-and-spirits"),
    path('display/club-mate.html', display_club_mate,
         name="display-club-mate"),
    path('display/soft-drinks.html', display_soft_drinks,
         name="display-soft-drinks"),
    path('display/progress.html', display_progress,
         name="display-progress"),
]
