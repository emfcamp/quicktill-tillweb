from django.db.models import Q
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

import emf.models

from quicktill.models import *
from .tilldb import *

def current_time():
    # Override this when testing!
    # return datetime.datetime(2022, 6, 1, 17, 0, 0)
    return datetime.datetime.now()


class EventInfo:
    def __init__(self, now):
        # Work out how far through the event we are, based on the
        # supplied time.
        self.now = now
        sessions = emf.models.Session.objects.all()

        self.length = datetime.timedelta()
        self.total_consumption = 0.0
        self.time_passed = datetime.timedelta()
        self.expected_consumption = 0.0
        self.open = False
        self.next_open = None
        self.closes_at = None
        for s in sessions:
            start = s.opening_time
            end = s.closing_time
            weight = s.weight
            self.length += s.length
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
        if sessions:
            self.completed_fraction = self.time_passed / self.length
            self.completed_pct = self.completed_fraction * 100.0
            self.completed_pct_remainder = 100.0 - self.completed_pct
            self.expected_consumption_fraction = self.expected_consumption \
                / self.total_consumption
            self.expected_consumption_pct = self.expected_consumption_fraction \
                * 100.0
            self.expected_consumption_pct_remainder = 100.0 \
                - self.expected_consumption_pct
        else:
            self.completed_fraction = 0.0
            self.completed_pct = 0.0
            self.completed_pct_remainder = 100.0
            self.expected_consumption_fraction = 0.0
            self.expected_consumption_pct = 0.0
            self.expected_consumption_pct_remainder = 100.0


# We use this date format in templates - defined here so we don't have
# to keep repeating it.  It's available in templates as 'dtf'
dtf = "Y-m-d H:i"


@login_required
def refusals(request):
    with tillsession() as s:
        r = s.query(RefusalsLog)\
             .options(joinedload('user'))\
             .order_by(RefusalsLog.id)\
             .all()
        return render(request, 'emf/refusals.html',
                      context={'refusals': r,
                               'dtf': dtf,
                      })


def display(request, page=None):
    return render(request, 'emf/display.html')


def display_info(request):
    now = current_time()

    # Work out whether we are open
    sessions = emf.models.Session.objects.filter(
        closing_time__gt=now)
    currently_open = False
    for s in sessions:
        if s.opening_time < now:
            currently_open = True

    # Fetch pages
    pages = emf.models.DisplayPage.objects.filter(
        Q(display_after=None) | Q(display_after__lt=now),
        Q(display_until=None) | Q(display_until__gt=now),
        enabled=True,
        condition__in=('A', 'O' if currently_open else 'C')).all()

    urgent = [ p for p in pages if p.priority == 'U' ]

    if urgent:
        # The only pages are urgent pages
        pages = [ p.as_dict() for p in urgent ]
    else:
        pages = [ p.as_dict() for p in pages ]

    if not pages:
        # Display is blank!
        return JsonResponse({
            'name': 'blank',
            'header': ' ',
            'content': ' ',
            'duration': 5000 if settings.DEBUG else 30000,
            'page': 'Idle',
        })

    current = request.GET.get("current", "start")

    pagenum = 0
    for pn, p in enumerate(pages):
        if p['name'] == current:
            pagenum = pn + 1
            break

    if pagenum >= len(pages):
        pagenum = 0

    page = pages[pagenum]
    page['page'] = f"Page {pagenum + 1} of {len(pages)}" \
        if len(pages) > 1 else ""

    if callable(page['content']):
        page['content'] = page['content']()

    page['duration'] = 5000 if settings.DEBUG else page['duration'] * 1000

    return JsonResponse(page)


def display_page_info(request, page):
    try:
        page = emf.models.DisplayPage.objects.get(slug=page)
    except emf.models.DisplayPage.DoesNotExist:
        raise Http404

    page = page.as_dict()
    if callable(page['content']):
        page['content'] = page['content']()
    page['duration'] = 5000
    page['page'] = "Page n of m"

    return JsonResponse(page)


def frontpage(request):
    with tillsession() as s:
        info = EventInfo(current_time())

        alcohol_used, total_alcohol, alcohol_used_pct = booziness(s)

        ales, kegs, ciders = on_tap(s)

        sessions = emf.models.Session.objects.filter(
            closing_time__gt=current_time())

        return render(request, "emf/whatson.html",
                      {"info": info,
                       "alcohol_used": alcohol_used,
                       "total_alcohol": total_alcohol,
                       "alcohol_used_pct": alcohol_used_pct,
                       "alcohol_used_pct_remainder": 100.0 - alcohol_used_pct,
                       "sessions": sessions,
                       "ales": ales,
                       "kegs": kegs,
                       "ciders": ciders,
                      })


def locations_json(request):
    with tillsession() as s:
        locations = [x[0] for x in s.query(distinct(StockLine.location))
                     .order_by(StockLine.location).all()]
        return JsonResponse({'locations': locations})


def location_json(request, location):
    with tillsession() as s:
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
    with tillsession() as s:
        stock = s.query(StockType)\
                 .filter(StockType.remaining > 0)\
                 .order_by(StockType.dept_id)\
                 .order_by(StockType.manufacturer)\
                 .order_by(StockType.name)\
                 .all()
        return JsonResponse(
            {'stock': [{
                'description': s.format(),
                'remaining': s.remaining,
                'unit': s.unit.name,
            } for s in stock]})


def progress_json(request):
    with tillsession() as s:
        alcohol_used, total_alcohol, alcohol_used_pct = booziness(s)
        info = EventInfo(current_time())

        return JsonResponse(
            {'licensed_time_pct': info.completed_pct,
             'expected_consumption_pct': info.expected_consumption_pct,
             'actual_consumption_pct': (alcohol_used / total_alcohol) * 100,
            })


def sessions_json(request):
    sessions = emf.models.Session.objects.all()
    return JsonResponse(
        {'sessions': [
            { k: getattr(s, k) for k in ('opening_time', 'closing_time') }
            for s in sessions ],
        })
