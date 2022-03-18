import datetime

import selenium.common.exceptions
import urllib3
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import kiwirecorder
import os

class KiwiSDR:
    @staticmethod
    def getLink(region, frequency, mode):
        link = "http://s.printf.cc/"
        regions = {"North America": "n", "Asia": "a", "Pacific": "p", "Mediterranean": "m", "East Asia": "a"}
        link += f"#{regions[region]}/"
        link += str(frequency)
        link += mode
        return link

    def navigate(self, redirector):
        # Navigate the headless webdriver to a URL
        print("Navigating to " + redirector)

        try:
            self.driver.get(redirector)

#        except (selenium.common.exceptions.InvalidSessionIdException, ConnectionError,
#                selenium.common.exceptions.WebDriverException, ConnectionRefusedError,
#                urllib3.exceptions.MaxRetryError):
        except:
            # Restart the browser and try again
            print("InvalidSessionID or connection issues, restarting the browser and trying again")
            self.driver.close()
            self.quit()
            print("Launching new browser...")
            self.driver = webdriver.Firefox(self.path_to_webdriver, options=self.options)

            # try again
            time.sleep(5)
            self.navigate(redirector)

        self.driver.refresh()
        time.sleep(self.load_time)  # Give time for the page to fully load

    def find_server_and_port(self):
        # Extract the website and port number from the current page (which must be a KiwiSDR link)

        raw_url = self.driver.current_url

        print("Connected to " + raw_url)
        server_and_port = raw_url.split(":")
        server_and_port.pop(0)  # remove the http:// or https://
        server = server_and_port[0].strip("/")
        port = server_and_port[1].split("/?f")[0]

        return server, port

    def record(self, mode, frequency, name, time_to_record_for, start_time):
        # Call kiwirecorder to record a transmission

        server, port = self.find_server_and_port()
        print("Starting recording")
        print(datetime.datetime.utcnow())
        print(start_time)

        self.quit()
        kiwirecorder.record(server, port, name, frequency, mode, time_to_record_for, start_time, self.out_directory)

    def quit(self):
        # Kill all of the children so we don't leave Firefox orphans laying around
        self.driver.close()
        self.driver.quit()

    def __init__(self, path_to_webdriver, out_directory, load_time=7, debug=False):
        self.load_time = load_time  # How long to wait for the Pavlova/kiwiSDR interface to load
        self.path_to_webdriver = path_to_webdriver
        self.options = Options()
        self.out_directory = out_directory

        if not debug:
            self.options.headless = True

        self.options.set_preference("media.volume_scale", "0.0")
        os.chdir(path_to_webdriver)
        self.driver = webdriver.Firefox(path_to_webdriver, options=self.options)