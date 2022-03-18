from django.urls import path, include
from tillweb_infra import emfviews

emfurls = [
    path('', emfviews.frontpage, name="frontpage"),
    path('locations.json', emfviews.locations_json, name="locations-json"),
    path('location/<location>.json', emfviews.location_json,
         name="location-json"),
    path('stock.json', emfviews.stock_json, name="stock-json"),
    path('progress.json', emfviews.progress_json, name="progress-json"),
    path('refusals/', emfviews.refusals, name="refusals"),
    path('display/on-tap.html', emfviews.display_on_tap, name="display-on-tap"),
    path('display/cans-and-bottles.html', emfviews.display_cans_and_bottles,
         name="display-cans-and-bottles"),
    path('display/wines-and-spirits.html', emfviews.display_wines_and_spirits,
         name="display-wines-and-spirits"),
    path('display/club-mate.html', emfviews.display_club_mate,
         name="display-club-mate"),
    path('display/soft-drinks.html', emfviews.display_soft_drinks,
         name="display-soft-drinks"),
    path('display/progress.html', emfviews.display_progress,
         name="display-progress"),
]
