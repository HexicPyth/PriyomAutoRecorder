import datetime
import time
import KiwiSDR
import traceback


class Recorder:
    def connect_to_kiwi(self, name, frequency, mode, known_region, start_time,
                        specified_record_time=None, attempts=1,):
        try:

            if known_region:
                region = known_region
            else:
                try:
                    region = self.stations_to_regions[name.lower()]
                except KeyError:
                    print(f"{name} not found in stations-->region dictionary, assuming Mediterranean")
                    region = "Mediterranean"

            print(f"{name} = {region}")
            pavlov_dispatcher_link = self.kiwisdr.getLink(region, frequency, mode.lower())
            self.kiwisdr.navigate(pavlov_dispatcher_link)

            try:
                if specified_record_time:
                    record_time = 60*specified_record_time
                else:
                    record_time = 60*self.stations_to_transmission_lengths[name.lower()]

            except KeyError:
                print(f"RecorderThread: {name} not found in station-->transmission"
                      f" length dictionary; assuming 20 minutes")

                record_time = 20*60

            print("Recording " + name + " for " + str(int(record_time/60)) + " minutes")
            try:
                self.kiwisdr.record(mode, frequency, name, record_time, start_time)

            except IndexError:
                if attempts < 10:
                    print(f"RecorderThread: All kiwis busy; trying again in 15s (Attempt {attempts}/10)")
                    time.sleep(15)
                    self.connect_to_kiwi(name, frequency, mode, known_region, start_time,
                                         specified_record_time=specified_record_time, attempts=attempts+1)
                else:
                    print(f"Error: All kiwis busy; Giving up on recording {name} after trying to connect 10 times...")

        except OSError:
            traceback.print_exc()

    def record(self, calendarmonitor):
        current_time = datetime.datetime.utcnow().replace(microsecond=0)

        next_station = self.next_station
        start_time = next_station[4]

        name, frequency, mode, known_region, start_time, specified_record_time = self.next_station

        if start_time > current_time:
            delta_t = (start_time - current_time).seconds

            if not calendarmonitor.debug:
                print(f"RecorderThread: {name} starts in {delta_t} seconds; sleeping for {delta_t - 30}")
                time.sleep(delta_t - 30)
                print("RecorderThread: Recording....")
                self.connect_to_kiwi(name, frequency, mode, known_region, start_time, specified_record_time)

            else:
                print("RecorderThread: Recording....")
                self.connect_to_kiwi(name, frequency, mode, known_region, start_time, specified_record_time)

        else:
            delta_t = (current_time - start_time).seconds
            print(f"RecorderThread: {name} started {delta_t} seconds ago; recording now...")
            self.connect_to_kiwi(name, frequency, mode, known_region, start_time, specified_record_time)

        print(f"RecorderThread: Recording of {name} finished; Recorder thread quitting;")
        return

    def __init__(self, calendarmonitor, station_info, out_directory):
        # station_info = [name, frequency, mode, known_region, start_time, specified_record_time]
        self.calendarmonitor = calendarmonitor

        self.stations_to_regions = calendarmonitor.stations_to_regions
        self.stations_to_transmission_lengths = calendarmonitor.stations_to_transmission_lengths

        self.kiwisdr = KiwiSDR.KiwiSDR(self.calendarmonitor.geckodriver_path, out_directory, load_time=10,
                                       debug=self.calendarmonitor.debug)
        self.next_station = station_info

