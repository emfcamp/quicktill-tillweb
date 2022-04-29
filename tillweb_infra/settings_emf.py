from datetime import datetime
# start, end, weight
EVENT_TIMES = [
    # Thursday evening
    (datetime(2022, 6, 2, 18, 0), datetime(2022, 6, 2, 23, 30), 1.0),
    # Friday all day until late
    (datetime(2022, 6, 3, 11, 0), datetime(2022, 6, 4, 1, 30), 2.0),
    # Saturday all day until late
    (datetime(2022, 6, 4, 11, 0), datetime(2022, 6, 5, 1, 30), 2.0),
    # Sunday until 0030
    (datetime(2022, 6, 5, 11, 0), datetime(2022, 6, 6, 0, 30), 1.0),
]
