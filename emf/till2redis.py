# This module implements a command line program that connects to the
# till database and to redis, listens for notifications from the till
# database and pushes updated objects to redis. It is expected that a
# single instance of this program will be run as a daemon.

import redis
import sdnotify
from . import tilldb  # noqa
import sqlalchemy.event
from sqlalchemy.orm import joinedload, undefer
from django.core.serializers.json import DjangoJSONEncoder
from quicktill import event, listen, td
from quicktill.models import StockLine, StockType, StockItem
from .api_objects import stockline_to_dict, stocktype_to_dict, stockitem_to_dict

rcon = None
json = DjangoJSONEncoder(indent=2)


qcounter_enabled = True
show_queries = False


class qcounter:
    def __init__(self, task=None):
        self.queries = []
        self.session = td.s
        self.task = task

    def __enter__(self):
        if qcounter_enabled:
            sqlalchemy.event.listen(
                self.session.get_bind(), "before_cursor_execute",
                self._querylog_callback)

    def __exit__(self, type, value, traceback):
        if qcounter_enabled:
            sqlalchemy.event.remove(
                self.session.get_bind(), "before_cursor_execute",
                self._querylog_callback)
            print(f"{self.task or ''} -> {len(self.queries)} queries used")
            if show_queries:
                for n, q in enumerate(self.queries, start=1):
                    print(f"{n}: {q}")

    def _querylog_callback(self, _conn, _cur, query, params, *_):
        self.queries.append(query)


def publish(d):
    text = json.encode(d)
    rcon.set(d['key'], text)


def delete(key):
    rcon.delete(key)


def notify_stockline_change(id_str):
    try:
        id = int(id_str)
    except Exception:
        return
    with td.orm_session():
        with qcounter("stockline_change"):
            sl = td.s.query(StockLine)\
                     .options(joinedload("stockonsale"),
                              joinedload("stockonsale.stocktype"),
                              undefer("stockonsale.remaining"),
                              undefer("stockonsale.stocktype.total_remaining"),
                              undefer("stockonsale.stocktype.total"))\
                     .get(id)
            if not sl:
                delete(f"stockline/{id}")
                return
            publish(stockline_to_dict(sl))


def notify_stocktype_change(id_str):
    try:
        id = int(id_str)
    except Exception:
        return
    with td.orm_session():
        with qcounter("stocktype_change"):
            st = td.s.query(StockType)\
                     .options(joinedload("items"),
                              joinedload("items.stockline"),
                              joinedload("items.stockline.stockonsale"),
                              joinedload("meta"),
                              undefer("total_remaining"),
                              undefer("total"),
                              undefer("items.remaining"))\
                     .get(id)
            if not st:
                delete(f"stocktype/{id}")
                return
            publish(stocktype_to_dict(st))
            # All items of this stocktype will have changed as well
            for si in st.items:
                publish(stockitem_to_dict(si))
                # If the item is connected to a stockline, that stockline will
                # also have changed
                if si.stockline:
                    publish(stockline_to_dict(si.stockline))


def notify_stockitem_change(id_str):
    try:
        id = int(id_str)
    except Exception:
        return
    with td.orm_session():
        with qcounter("stockitem_change"):
            si = td.s.query(StockItem)\
                     .options(undefer("remaining"),
                              joinedload("stocktype"),
                              joinedload("stockline"),
                              joinedload("stockline.stockonsale"),
                              undefer("stocktype.total_remaining"),
                              undefer("stocktype.total"))\
                     .get(id)
            if not si:
                delete(f"stockitem/{id}")
                return
            publish(stockitem_to_dict(si))
            # The item being connected to or disconnected from a
            # stockline is already covered by stockline_change
            # notifications. Updates to amount remaining are not;
            # publish an update here and live with duplicate
            # notifications.
            if si.stockline:
                publish(stockline_to_dict(si.stockline))


def main():
    global rcon
    td.init("dbname=emfcamp")
    mainloop = event.SelectorsMainLoop()
    listener = listen.db_listener(mainloop, td.engine)
    rcon = redis.Redis(decode_responses=True)

    # Start listening
    listener.listen_for("stockline_change", notify_stockline_change)
    listener.listen_for("stocktype_change", notify_stocktype_change)
    listener.listen_for("stockitem_change", notify_stockitem_change)

    # Preload redis with the current state of all the objects we can publish

    with td.orm_session():
        with qcounter("init"):
            stocktypes = td.s.query(StockType)\
                             .options(joinedload("unit"))\
                             .options(joinedload("meta"))\
                             .options(undefer("total"),
                                      undefer("total_remaining"))\
                             .all()
            stockitems = td.s.query(StockItem)\
                             .options(undefer("remaining"))\
                             .all()
            stocklines = td.s.query(StockLine)\
                             .options(joinedload("stockonsale"))\
                             .all()

            for sl in stocklines:
                publish(stockline_to_dict(sl))
            for st in stocktypes:
                publish(stocktype_to_dict(st))
            for si in stockitems:
                publish(stockitem_to_dict(si))

    # Notify systemd that startup is complete
    sdnotify.SystemdNotifier().notify("READY=1")

    # Loop forever (or until the database or redis is restarted)
    while True:
        mainloop.iterate()
