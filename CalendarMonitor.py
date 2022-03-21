import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import datetime
import time
import KiwiSDR
import string
import traceback
import queue
import recorderthread
import threading
import os
from selenium import common


class CalendarMonitor:

    @staticmethod
    def round_minutes(some_datetime, step):
        """ round up to nearest step-minutes
        Written by David Chan from StackOverflow
        https://stackoverflow.com/a/55013608"""

        change = datetime.timedelta(
            minutes=some_datetime.minute % step,
            seconds=some_datetime.second,
            microseconds=some_datetime.microsecond)

        if change > datetime.timedelta():
            change -= datetime.timedelta(minutes=step)

        return some_datetime - change

    def find_start_time(self, time_remaining_string):
        _words = time_remaining_string.split(" ")[-2:]
        current_time = datetime.datetime.utcnow()

        print(_words)
        print(f"Current time: {current_time}")

        if ("MINUTES" in _words) or ("MINUTE" in _words) or ("SECONDS" in _words) or ("HOURS" in _words):
            try:
                if _words[1] == "HOURS":
                    minutes_remaining = int(_words[0] * 60)
                    start_time = current_time + datetime.timedelta(minutes=minutes_remaining)

                if _words[1] == "MINUTE":
                    minutes_remaining = 1
                    start_time = current_time + datetime.timedelta(minutes=minutes_remaining)
                    if start_time.second != 0:
                        # Subtract a second so that if this code runs exactly 15s before a station we don't miss it

                        start_time = start_time - datetime.timedelta(seconds=1)

                elif _words[1] == "SECONDS":
                    start_time = current_time + datetime.timedelta(seconds=1)  # START LIKE, NOW!!!
                    start_time = start_time.replace(second=0).replace(microsecond=0)
                    start_time = self.round_minutes(start_time, 5)
                    return start_time

                else:  # X MINUTES REMAINING
                    minutes_remaining = int(_words[0])
                    start_time = current_time + datetime.timedelta(minutes=minutes_remaining)
                    start_time = start_time - datetime.timedelta(seconds=30)
                    start_time = start_time.replace(second=0).replace(microsecond=0)
            except OverflowError:
                start_time = current_time + datetime.timedelta(seconds=30)

            # print(f"{minutes_remaining} minutes remaining")
            start_time = self.round_minutes(start_time, 5)
            print("Starting at " + str(start_time))

            return start_time

    def launch_recorder_thread(self, station_info, out_directory):
        print(f"Launching a new thread to record {station_info[0]} at {station_info[4]}\n")
        recorder_thread = recorderthread.Recorder(self, station_info, out_directory)
        recorder_thread.record(self)

    @staticmethod
    def split_stations(_words):
        stations = []
        previous_index = 0
        _words[len(_words) - 1] += "\n"  # Make the multiple-station detector detect the final station too
        for index, item in enumerate(_words):
            if "\n" in item:
                station = _words[previous_index:index]
                station.append(item.split("\n")[0])
                _words[index] = item.split("\n")[1]
                previous_index = index
                print(f"Found station: {station}")
                stations.append(station)

        return stations

    def find_next_station(self):
        # If the user specified a station to immediately start recording, do that, and then operate normally
        # from the Priyom calendar after the recording is complete.

        # Scrape calendar data from priyom.org
        try:
            next_station = self.driver.find_element_by_xpath("/html/body/div/div[1]/main/section/div[2]/ul/li").text
            time_remaining = self.driver.find_element_by_xpath("/html/body/div/div[1]/main/section/div[2]/h3").text
        except common.exceptions.WebDriverException:
            traceback.print_exc()
            self.driver.quit()
            print("webdriver died, relaunching")
            self.driver = self.start_webdriver(self.options)
            return None

        stations_info = []
        words = next_station.split(" ")

        words = self.split_stations(words)
        for station in words:

            # Some stations have "(in case of traffic)" written next to the frequency. This will mess up the
            # code we use to extract the frequency and mode, so get rid of it.
            try:
                station.remove("(In")
                station.remove("case")
                station.remove("of")
                station.remove("traffic)")
            except ValueError:
                pass

            # Check to see if the station has a listed target, and use it if it does
            if len(station) > 3 and "used:" not in next_station:  # It has a listed target
                target = str(station[-1::])
                specified_region = ''.join(char for char in target if char in string.ascii_letters)

                # North America is two words so the first word will be truncated
                # AFAIK there are no South America-beamed transmissions, so this is fine
                if specified_region == "America":
                    specified_region = "North America"

                print("Target found!", specified_region)
            else:
                specified_region = None

            name = station[0]
            frequency = station[1].strip("kHz")
            mode = station[2]

            if mode == "USB/AM" or "LSB/AM":
                mode = mode[:3]

            if mode == "RTTY" or mode == "RTT":
                frequency = str(int(frequency) - 2)
                mode = "USB"

            stations_info.append([name, frequency, mode, time_remaining])

        print(stations_info)
        return stations_info

    @staticmethod
    def sleep_until_next_station(seconds):
        time_left = seconds
        time_slept = 0

        while time_left > 0:
            time.sleep(30)
            time_left -= 30
            time_slept += 30

            if time_slept % 60 == 0:
                print(f"Calendarmonitor still sleeping; {time_left} seconds left")

    def loop(self, out_directory, debug=False, start=None):
        specified_record_time = None  # This doesnt do anything rn

        try:
            while True:

                # [name, frequency, mode, time_remaining, region]
                station_info = self.find_next_station()
                seconds_to_start_time = 0

                for station in station_info:
                    time.sleep(1)

                    name, frequency, mode, time_remaining = station
                    if len(station) > 4:
                        specified_region = station[4]
                    else:
                        specified_region = None

                    if (name, frequency, mode, time_remaining, specified_region) and "Search" not in frequency:
                        start_time = self.find_start_time(time_remaining)

                        if start_time:
                            current_time = datetime.datetime.utcnow()

                            try:
                                if start_time > current_time:
                                    seconds_to_start_time = (start_time - current_time).seconds
                                else:
                                    seconds_to_start_time = 0

                            except OverflowError:
                                seconds_to_start_time = 0

                            print(start_time)

                            station_info = [name, frequency, mode, specified_region, start_time, specified_record_time]

                            recorder_thread = threading.Thread(target=self.launch_recorder_thread,
                                                               args=(station_info, out_directory), name='recorderThread')

                            recorder_thread.start()

                            time_to_resume = datetime.datetime.utcnow() + \
                                             datetime.timedelta(seconds=seconds_to_start_time + 30)

                            print(f"Recording of {name} @ {frequency}kHz {mode.upper()} queued for {start_time};"
                                  f" sleeping until {time_to_resume}...")


                        else:
                            print("Nothing coming up soon...")
                    else:
                        print("Nothing coming up soon...")

                if seconds_to_start_time != 0:
                    self.sleep_until_next_station(seconds_to_start_time + 30)

                time.sleep(12)

        except KeyboardInterrupt:
            self.quit()

    def quit(self):
        self.driver.close()
        self.driver.quit()
        self.kiwisdr.quit()

    def start_webdriver(self, options):
        driver = webdriver.Firefox(executable_path=self.geckodriver_path, options=options)
        driver.get("http://www.priyom.org")
        return driver

    def __init__(self, out_directory, geckodriver_path="C:\\Users\\user\\PycharmProjects\\PriyomAutoRecorder\\", debug=False):
        self.kiwisdr = KiwiSDR.KiwiSDR(geckodriver_path, out_directory, load_time=10, debug=debug)
        self.options = Options()
        self.options.headless = True

        self.geckodriver_path = geckodriver_path
        self.driver = self.start_webdriver(self.options)
        self.recording_queue = queue.Queue()
        self.debug = debug
        self.link = '/html/body/div/div[1]/main/section/div[2]/ul'

        self.stations_to_regions = \
            {"hm01": "North America", "e11": "Mediterranean", "s11a": "Mediterranean", "m14": "Mediterranean",
             "p03h": "Mediterranean", "f03l": "Mediterranean", "f03j": "Mediterranean", "f06": "Mediterranean",
             "m12": "Mediterranean", "e06": "Mediterranean", "s06s": "Mediterranean", "m23": "Mediterranean",
             "xpa2": "Pacific", "xpb": "Mediterranean", "v13": "Asia", "f01": "Asia", "m01": "Mediterranean",
             "s06": "Mediterranean", "E11": "Mediterranean", "P03": "Mediterranean", "P03k": "Mediterranean"}

        self.stations_to_transmission_lengths = \
            {"hm01": 29, "e11": 12, "s11a": 10, "e06": 20, "s06": 20, "m01": 10, "m14": 15, "p03h": 5, "f03l": 4,
             "f03j": 5, "f06": 16, "m12": 15, "s06s": 10, "m23": 20, "xpa2": 10, "xpb": 10, "v13": 20, "f01": 16,
             "E07": 10, "P03": 10, "P03k": 10, "P03e":  10, "f03d": 5, "f03k": 5, "f06a": 5}