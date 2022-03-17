import datetime
import os
import kiwirecorder
import time
import recorderthread
import CalendarMonitor
import threading

os.chdir('./kiwiclient-master')
start_time = datetime.datetime.utcnow()
calendarmonitor = CalendarMonitor.CalendarMonitor()


def recorder_thread(station_info):
    print("Starting...")
    recorder = recorderthread.Recorder(calendarmonitor, station_info)
    recorder.record(calendarmonitor)


def launch_recorder_thread(station_info):
    recorder = threading.Thread(target=recorder_thread, args=(station_info,), name='recorderThread')
    recorder.start()


station_info = ["ThreadSafeWriteTest", "6000", "am", None, start_time, 1]
launch_recorder_thread(station_info)
time.sleep(1)
launch_recorder_thread(station_info)