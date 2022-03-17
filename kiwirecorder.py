import os
import datetime
import subprocess
import os.path


def normalize_time(month, day, hour, minute, round_to_nearest_5m=True):
    if int(month) <= 9:
        month = "0" + month
    if int(day) <= 9:
        day = "0" + day
    if int(hour) <= 9:
        hour = "0" + hour
    if int(minute) <= 9:
        minute = "0" + minute

    return [month, day, hour, minute]


def generate_timestamp(time):
    print("Generating timestamp for " + str(time))
    month = str(time.month)
    day = str(time.day)
    year = str(time.year)[-2::]
    hour = str(time.hour)
    minute = str(time.minute)
    month, day, hour, minute = normalize_time(month, day, hour, minute)

    return str(month + day + year + "_" + hour + minute)


def launch_kiwiclient(server, port, frequency, mode, filename, out_directory, time):

    args = ['python', 'kiwirecorder.py', '-s', server, '-p', str(port), '-f', str(frequency), '-m', mode,
            '--filename', filename, '--time-limit', f'{time+1}', '--dir', out_directory]
    for item in args:
        print(item + " ", end='')

    os.chdir(out_directory)
    output_file = out_directory + filename + ".wav"
    file_already_exists = os.path.exists(output_file)
    print(os.listdir())

    this_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(this_dir)
    os.chdir("./kiwiclient-master")

    print("File exists: " + str(file_already_exists))
    if not file_already_exists:
        print("\n" + output_file + " doesn't exist; recording...")
        process = subprocess.Popen(args)

    else:
        print("Error: " + output_file + " already exists; is another recording of this station currently in progress?")
        return

    # Sometimes the --time-limit argument sporadically doesn't work; This will just forcefully kill kiwirecorder
    # at the time limit in case it isn't already dead...
    try:
        print(f"Recording for {time} seconds... (PID={process.pid})")
        process.wait(timeout=time)
    except subprocess.TimeoutExpired:
        print('Time is up... killing', process.pid)
        process.kill()
    print("Done")


def record(server, port, name, frequency, mode, time, start_time, out_directory):
    current_directory = os.path.realpath(os.getcwd())
    this_dir = os.path.dirname(os.path.realpath(__file__))

    # Switch to the directory containing this file
    os.chdir(this_dir)
    os.chdir("./kiwiclient-master")

    timestamp = generate_timestamp(start_time)
    filename = name + "_" + timestamp

    frequency = frequency.strip(',').strip("kHz")

    launch_kiwiclient(server, port, frequency, mode, filename, out_directory, time)
    os.chdir(current_directory)
