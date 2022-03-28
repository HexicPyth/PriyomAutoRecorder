import datetime
import os

start_time = datetime.datetime.utcnow()
next_day = {"Monday": "Tuesday", "Tuesday": "Wednesday", "Wednesday": "Thursday", "Thursday": "Friday",
            "Friday": "Saturday", "Saturday": "Sunday", "Sunday": "Monday"}


def find_todays_stations():
    this_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(this_dir)

    custom_schedules = [station.split(" ") for station in open("CustomCalendar.txt", "r").readlines()]
    custom_schedules.pop(0)  # Remove the "Name Frequency Region/Target Day Time" line
    stations = []

    for station in custom_schedules:
        _name = station[0]

        if "," in station[1]:
            _frequencies = station[1].split(',')

        else:
            _frequencies = station[1]

        _region = station[2]
        if "weekdays" in station[3].lower():
            _days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        elif "weekends" in station[3].lower():
            _days = ["Saturday, Sunday"]
        elif "everyday" in station[3].lower():
            _days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        else:
            _days = station[3]

        _time = station[4]
        for _frequency in _frequencies:
            for _day in _days:
                current_time = datetime.datetime.utcnow()
                day_of_week = current_time.strftime("%A")

                if _day == day_of_week:
                    year = current_time.year
                    month = current_time.month
                    day = current_time.day
                    hour = int(_time.split(":")[0])
                    minute = int(_time.split(":")[1])
                    start_time = datetime.datetime(year, month, day, hour, minute, 00)

                    _station = [_name, _frequency, _region, start_time]
                    stations.append(_station)

                # We check for the next days stations sometime in the 0'th hour UTC, so we need to include these in
                # the previous day to not miss them
                if _day == next_day[day_of_week] and _time.split(":")[0] == "00":
                    year = current_time.year
                    month = current_time.month
                    day = (current_time + datetime.timedelta(days=1)).day
                    hour = int(_time.split(":")[0])
                    minute = int(_time.split(":")[1])
                    start_time = datetime.datetime(year, month, day, hour, minute, 00)

                    _station = [_name, _frequency, _region, start_time]
                    stations.append(_station)
    return stations


def find_next_station():
    todays_stations = find_todays_stations()
    current_time = datetime.datetime.utcnow()

    next_station = []
    time_to_station_after_next_station = 0

    _next_stations = [station for station in todays_stations if current_time < station[3]]
    next_stations = []
    next_stations.append(_next_stations[0])

    future_stations_checked = 0
    for station in _next_stations:
        if station[3] == next_stations[0][3] and station not in next_stations:
            next_stations.append(station)

        elif future_stations_checked == 0:
            time_to_station_after_next_station = (current_time - station[3]).seconds - 30
            future_stations_checked += 1

    return next_stations, time_to_station_after_next_station
