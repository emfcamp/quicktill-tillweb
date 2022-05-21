from contextlib import contextmanager
from django.conf import settings
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


# Context manager for till database sessions
@contextmanager
def tillsession():
    s = settings.TILLWEB_DATABASE()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


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

    ales = base.filter(StockType.dept_id == 10).all()

    kegs = base.filter(StockType.dept_id.in_([20, 100, 105])).all()

    ciders = base.filter(StockType.dept_id == 30).all()

    return ales, kegs, ciders


