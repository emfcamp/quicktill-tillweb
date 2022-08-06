from .tilldb import tillsession, on_tap
from quicktill.models import StockType, Unit, Department, PriceLookup
from sqlalchemy.orm import undefer, joinedload
from django.http import JsonResponse, Http404


# Convert various till models to dicts to output as json

def department_to_dict(d):
    return {
        'id': d.id,
        'description': d.description,
        'notes': d.notes,
    }


def stocktype_to_dict(s):
    return {
        'id': s.id,
        'department': department_to_dict(s.department),
        'manufacturer': s.manufacturer,
        'name': s.name,
        'abv': s.abv,
        'fullname': format(s),
        'price': s.saleprice,
        'base_units_bought': s.total,
        'base_units_remaining': s.remaining,
        'base_unit': s.unit.name,
        'sale_unit': s.unit.item_name,
        'base_units_per_sale_unit': s.unit.units_per_item,
    }


def stockitem_to_dict(s, remain_fraction=None):
    d = {
        'id': s.id,
        'stocktype_id': s.stocktype_id,
        'manufacturer': s.stocktype.manufacturer,
        'name': s.stocktype.name,
        'abv': s.stocktype.abv,
        'fullname': format(s.stocktype),
        'price': s.stocktype.saleprice,
        'remaining_pct': None,
    }
    if remain_fraction is not None:
        d['remaining_pct'] = remain_fraction * 100
    return d


def plu_to_dict(plu):
    return {
        'id': plu.id,
        'description': plu.description,
        'note': plu.note,
        'department': department_to_dict(plu.department),
        'price': plu.price,
    }


# Partial queries

def stocktype_query(s):
    return s.query(StockType)\
            .join(Unit)\
            .filter(StockType.remaining > 0)\
            .order_by(StockType.dept_id)\
            .order_by(StockType.manufacturer)\
            .order_by(StockType.name)\
            .options(undefer('total'))\
            .options(undefer('remaining'))\


# Views


def departments(request):
    with tillsession() as s:
        depts = s.query(Department).order_by(Department.id).all()

        return JsonResponse({
            'departments': [department_to_dict(d) for d in depts],
        })


def api_on_tap(request):
    with tillsession() as s:
        ales, kegs, ciders = on_tap(s)

        return JsonResponse({
            'ales': [stockitem_to_dict(ale, rf) for ale, rf in ales],
            'kegs': [stockitem_to_dict(keg, rf) for keg, rf in kegs],
            'ciders': [stockitem_to_dict(cider, rf) for cider, rf in ciders],
        })


def cybar(request):
    with tillsession() as s:
        # We want all stock sold in cans or bottles
        stocktypes = stocktype_query(s)\
            .filter(Unit.name.in_(['can', 'bottle']))\
            .all()

        return JsonResponse({
            'cybar': [stocktype_to_dict(st) for st in stocktypes],
        })


def stock(request):
    with tillsession() as s:
        stocktypes = stocktype_query(s).all()

        return JsonResponse({
            'stocktypes': [stocktype_to_dict(st) for st in stocktypes],
        })


def shop(request):
    with tillsession() as s:
        # We want all price lookups in departments 210, 220, 230, 240
        plus = s.query(PriceLookup)\
                .filter(PriceLookup.dept_id.in_([210, 220, 230, 240]))\
                .order_by(PriceLookup.dept_id)\
                .order_by(PriceLookup.description)\
                .all()

        return JsonResponse({
            'shop': [plu_to_dict(plu) for plu in plus],
        })


def dept(request, dept_id):
    with tillsession() as s:
        stocktypes = stocktype_query(s)\
            .filter(StockType.dept_id == dept_id)\
            .all()

        return JsonResponse({
            'stocktypes': [stocktype_to_dict(st) for st in stocktypes],
        })


def stocktype(request, stocktype_id):
    with tillsession() as s:
        stocktype = s.query(StockType)\
                     .options(joinedload('unit'))\
                     .options(undefer('total'))\
                     .options(undefer('remaining'))\
                     .get(stocktype_id)

        if not stocktype:
            raise Http404

        return JsonResponse(stocktype_to_dict(stocktype))
