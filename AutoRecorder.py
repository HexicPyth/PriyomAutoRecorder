import CalendarMonitor
import traceback
import os

monitor = None
geckodriver_path = os.path.abspath("./")
output_path = "D:/Temp/"

try:
    monitor = CalendarMonitor.CalendarMonitor(output_path, debug=False)
    monitor.loop(output_path, debug=False)

# If literally anything happens, terminate all the firefox processes so we don't leave
# hundreds of orphaned webdrivers running
except (KeyboardInterrupt, IndexError, OSError, FileNotFoundError, TypeError):
    traceback.print_exc()
    print("An error occurred, quitting...")
    if monitor:
        monitor.quit()
    quit(1)
