from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import subqueryload, subqueryload_all
from sqlalchemy.orm import joinedload, joinedload_all
from sqlalchemy.orm import lazyload
from sqlalchemy.orm import defaultload
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import undefer, defer, undefer_group
from sqlalchemy import distinct
from sqlalchemy import func

from decimal import Decimal

import datetime
import django.utils.timezone

class EventInfo:
    def __init__(self, override_time=None):
        # Work out how far through the event we are, based on the current
        # time or on the supplied time.
        self.now = override_time or datetime.datetime.now()

        self.length = datetime.timedelta()
        self.total_consumption = 0.0
        self.time_passed = datetime.timedelta()
        self.expected_consumption = 0.0
        self.open = False
        self.next_open = None
        self.closes_at = None
        for start, end, weight in settings.EVENT_TIMES:
            self.length += (end - start)
            self.total_consumption += weight
            if self.now >= end:
                # This segment has passed.
                self.time_passed += (end - start)
                self.expected_consumption += weight
            elif self.now >= start and self.now < end:
                # We are in this segment.
                self.open = True
                self.closes_at = end
                self.time_passed += (self.now - start)
                self.expected_consumption += weight * (
                    (self.now - start) / (end - start))
            elif self.now < start and not self.next_open:
                self.next_open = start
        self.completed_fraction = self.time_passed / self.length
        self.completed_pct = self.completed_fraction * 100.0
        self.completed_pct_remainder = 100.0 - self.completed_pct
        self.expected_consumption_fraction = self.expected_consumption \
                                             / self.total_consumption
        self.expected_consumption_pct = self.expected_consumption_fraction \
                                        * 100.0
        self.expected_consumption_pct_remainder = 100.0 - self.expected_consumption_pct

def booziness(s):
    """How much booze have we used?

    Pass in an ORM session.  Returns tuple of amount of alcohol used
    and total amount of alcohol as Decimal, and percentage used as float
    """

    used_fraction = case([(StockItem.finished != None, 1.0)],
                    else_=StockItem.used / StockItem.size)

    # Amount of alcohol in stock item in ml.  The unit ID we're not listing
    # here is 'ml' which is size 1ml
    unit_alcohol = case([(Unit.name == 'pt', 568.0),
                        (Unit.name == '25ml', 25.0),
                        (Unit.name == '50ml', 50.0),
                        (Unit.name == 'can', 350.0),
                        (Unit.name == 'bottle', 330.0),
                        ], else_=1.0) * StockItem.size * StockType.abv / 100.0

    used, total = s.query(func.coalesce(func.sum(used_fraction * unit_alcohol), Decimal("0.0")),
                          func.coalesce(func.sum(unit_alcohol), Decimal("1.0")))\
                   .select_from(StockItem)\
                   .join(StockType)\
                   .join(Unit)\
                   .filter(StockType.abv != None)\
                   .one()

    return used, total, float(used / total) * 100.0

def on_tap(s):
    # Used in display_on_tap and frontpage
    base = s.query(StockItem, StockItem.remaining / StockItem.size)\
            .join('stocktype')\
            .join('stockline')\
            .filter(StockLine.location == "Bar")\
            .order_by(StockType.manufacturer, StockType.name)\
            .options(undefer('remaining'))\
            .options(contains_eager('stocktype'))

    ales = base.filter(StockType.dept_id == 1).all()

    kegs = base.filter(StockType.dept_id.in_([2, 13])).all()

    ciders = base.filter(StockType.dept_id == 3).all()

    return ales, kegs, ciders


from quicktill.models import *

# Monkeypatch the StockType class to have a "total" column so we can
# easily read total amounts of stuff ordered
StockType.total = column_property(
    select([func.coalesce(func.sum(StockItem.size), text("0.0"))],
           and_(StockItem.stocktype_id == StockType.id,
                Delivery.id == StockItem.deliveryid,
                Delivery.checked == True)).\
    correlate(StockType.__table__).\
    label('total'),
    deferred=True,
    doc="Total amount booked in")

# We use this date format in templates - defined here so we don't have
# to keep repeating it.  It's available in templates as 'dtf'
dtf = "Y-m-d H:i"

@login_required
def refusals(request):
    s = settings.TILLWEB_DATABASE()
    r = s.query(RefusalsLog)\
         .options(joinedload('user'))\
         .order_by(RefusalsLog.id)\
         .all()
    return render(request, 'emf/refusals.html',
                  context={'refusals': r,
                           'dtf': dtf,
                  })

def display_on_tap(request):
    s = settings.TILLWEB_DATABASE()
    ales, kegs, ciders = on_tap(s)

    return render(request, 'emf/display-on-tap.html',
                  context={'ales': ales, 'kegs': kegs, 'ciders': ciders})

def display_cans_and_bottles(request):
    s = settings.TILLWEB_DATABASE()
    # We want all stocktypes with unit 'can' or unit 'bottle', but only
    # if there are >0 qty remaining
    r = s.query(StockType)\
        .join(Unit)\
        .filter(Unit.name.in_(['can', 'bottle']))\
        .filter(StockType.remaining > 0.0)\
        .filter(StockType.abv != None)\
        .options(undefer('remaining'))\
        .order_by(StockType.manufacturer, StockType.name)\
        .all()

    return render(request, 'emf/display-cans-and-bottles.html',
                  context={'types': r})

def display_wines_and_spirits(request):
    s = settings.TILLWEB_DATABASE()
    wines = s.query(StockLine,
                    func.round(StockType.saleprice / (750/125), 1),
                    func.round(StockType.saleprice / (750/175), 1),
                    func.round(StockType.saleprice / (750/250), 1))\
             .join(StockType)\
             .filter(StockType.dept_id == 9)\
             .filter(StockType.remaining > 0.0)\
             .order_by(StockType.manufacturer, StockType.name)\
             .all()

    # We want all stocktypes with dept 4, but only
    # if there are >0 qty remaining
    spirits = s.query(StockType)\
               .filter(StockType.dept_id == 4)\
               .filter(StockType.remaining > 0.0)\
               .options(undefer('remaining'))\
               .order_by(StockType.manufacturer, StockType.name)\
               .all()

    return render(request, 'emf/display-wines-and-spirits.html',
                  context={'wines': wines, 'spirits': spirits})

def display_club_mate(request):
    s = settings.TILLWEB_DATABASE()
    mate = s.query(StockType, StockType.remaining, StockType.total,
                   StockType.remaining / StockType.total * 100.0)\
            .filter(StockType.manufacturer == "Club Mate")\
            .order_by(desc(StockType.name))\
            .all()

    return render(request, 'emf/display-club-mate.html',
                  context={'mate': mate})

def display_soft_drinks(request):
    s = settings.TILLWEB_DATABASE()
    soft = s.query(StockType, StockType.remaining / StockType.total * 100.0)\
            .filter(StockType.dept_id == 7)\
        .filter(StockType.remaining > 0.0)\
        .options(undefer('remaining'))\
        .order_by(StockType.manufacturer, StockType.name)\
        .all()

    return render(request, 'emf/display-soft-drinks.html',
                  context={'soft': soft})

def display_progress(request):
    s = settings.TILLWEB_DATABASE()
    alcohol_used, total_alcohol, alcohol_used_pct = booziness(s)
    info = EventInfo()

    return render(request, 'emf/display-progress.html',
                  context={
                      'info': info, 'alcohol_used': alcohol_used,
                      'total_alcohol': total_alcohol,
                      'alcohol_used_pct': alcohol_used_pct,
                      'alcohol_used_pct_remainder': 100.0 - alcohol_used_pct,
                  })

def frontpage(request):
    s = settings.TILLWEB_DATABASE()

    # Testing:
    #info = EventInfo(datetime.datetime(2018, 9, 1, 11, 30))
    # Production:
    info = EventInfo()

    alcohol_used, total_alcohol, alcohol_used_pct = booziness(s)

    ales, kegs, ciders = on_tap(s)

    return render(request, "emf/whatson.html",
                  {"info": info,
                   "alcohol_used": alcohol_used,
                   "total_alcohol": total_alcohol,
                   "alcohol_used_pct": alcohol_used_pct,
                   "alcohol_used_pct_remainder": 100.0 - alcohol_used_pct,
                   "ales": ales,
                   "kegs": kegs,
                   "ciders": ciders,
                  })

def locations_json(request):
    s = settings.TILLWEB_DATABASE()
    locations = [x[0] for x in s.query(distinct(StockLine.location))
                 .order_by(StockLine.location).all()]
    return JsonResponse({'locations': locations})

def location_json(request, location):
    s = settings.TILLWEB_DATABASE()
    lines = s.query(StockLine)\
             .filter(StockLine.location == location)\
             .order_by(StockLine.name)\
             .all()

    return JsonResponse({'location': [
        {"line": l.name,
         "description": l.sale_stocktype.format(),
         "price": l.sale_stocktype.saleprice,
         "price_for_units": l.sale_stocktype.unit.units_per_item,
         "unit": l.sale_stocktype.unit.name}
        for l in lines if l.stockonsale or l.linetype == "continuous"]})

def stock_json(request):
    s = settings.TILLWEB_DATABASE()
    stock = s.query(StockType)\
             .filter(StockType.remaining > 0)\
             .order_by(StockType.dept_id)\
             .order_by(StockType.manufacturer)\
             .order_by(StockType.name)\
             .all()
    return JsonResponse({'stock': [{
        'description': s.format(),
        'remaining': s.remaining,
        'unit': s.unit.name
        } for s in stock]})

def progress_json(request):
    s = settings.TILLWEB_DATABASE()
    alcohol_used, total_alcohol, alcohol_used_pct = booziness(s)
    info = EventInfo()

    return JsonResponse(
        {'licensed_time_pct': info.completed_pct,
         'expected_consumption_pct': info.expected_consumption_pct,
         'actual_consumption_pct': (alcohol_used / total_alcohol) * 100,
        })
