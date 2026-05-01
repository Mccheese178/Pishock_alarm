from datetime import datetime, timedelta
from time import sleep
from threading import Thread
from Pyshock import PishockAPI
import random
import os
import sys
from config import username, api_key, shocker_ids, app_name, test_mode, snooze_duration

pishock = PishockAPI(api_key, username, shocker_ids, app_name)
alarm_triggered = False
alarm_file = "alarm_time.txt"

def periodic_vibration():
    while not alarm_triggered:
        pishock.vibrate(0, 1)
        sleep(120)

def save_alarm_settings(alarm_time_str, intensity, duration):
    with open(alarm_file, "w") as file:
        file.write(f"{alarm_time_str} {intensity} {duration}")

def load_alarm_settings():
    if os.path.exists(alarm_file):
        with open(alarm_file, "r") as file:
            line = file.read().strip()
            alarm_time_str, intensity, duration = line.split()
            return alarm_time_str, int(intensity), int(duration)
    return None, None, None

def get_user_input():
    if not test_mode:
        alarm_time_str = input("Enter alarm time (24-hour HH:MM format): ")
    else:
        alarm_time_str = None

    intensity = input("Enter action intensity (1-100 or 'r' for random, '0' for beep): ")
    if intensity == 'r':
        intensity = random.randint(1, 100)
    else:
        intensity = int(intensity)
    shock_duration = input("Enter action duration (decibels allowed) (in seconds, 1-15, or 'r' for random): ")
    if shock_duration == "r":
        shock_duration = random.uniform(0, 15)
    else:
        shock_duration = float(intensity)

    return alarm_time_str, intensity, shock_duration

def calculate_time_until_alarm(alarm_time_str):
    now = datetime.now()
    alarm_time = datetime.strptime(alarm_time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
    if alarm_time < now:
        alarm_time += timedelta(days=1)
    return (alarm_time - now).total_seconds(), alarm_time

def execute_action(action, intensity, duration):
    global alarm_triggered
    if action == 's':
        pishock.shock(intensity, duration)
        print("\nShock delivered!")
    elif action == 'v':
        pishock.vibrate(intensity, duration)
        print("\nVibration delivered!")
    elif action == 'b':
        pishock.beep(duration)
        print("\nBeep sounded!")
    alarm_triggered = True

def check_for_time_left(remaining_seconds):
    while remaining_seconds > 0 and not alarm_triggered:
        sleep(60)
        remaining_seconds -= 60
        if remaining_seconds > 0:
            hours = int(remaining_seconds // 3600)
            minutes = int((remaining_seconds % 3600) // 60)
            seconds = int(remaining_seconds % 60)
            print(f"Time remaining: {hours} hours, {minutes} minutes, and {seconds} seconds.")

def snooze_alarm(action, intensity, duration):
    global alarm_triggered
    alarm_triggered = False
    print(f"Snoozing for {snooze_duration} minutes...")
    
    snooze_seconds = snooze_duration * 60
    time_thread = Thread(target=check_for_time_left, args=(snooze_seconds,))
    time_thread.start()
    vibration_thread = Thread(target=periodic_vibration)
    vibration_thread.start()

    sleep(snooze_seconds)
    execute_action(action, intensity, duration)
    time_thread.join()
    vibration_thread.join()

def execute_shock():
    global alarm_triggered

    saved_alarm_time, saved_intensity, saved_duration = load_alarm_settings()
    loaded_from_file = False
    
    if saved_alarm_time:
        use_saved = input(f"Saved alarm settings found ({saved_alarm_time}, {saved_intensity}, {saved_duration}). Would you like to load? (y/n): ").strip().lower()
        if use_saved == 'y':
            alarm_time_str = saved_alarm_time
            intensity = saved_intensity
            duration = saved_duration
            loaded_from_file = True
        else:
            alarm_time_str, intensity, duration = get_user_input()
    else:
        alarm_time_str, intensity, duration = get_user_input()

    print(f"Intensity set to {intensity}")
    print(f"Duration set to {round(duration, 2)}")

    action = input("Would you like to Shock, Vibrate, or Beep? (s for shock, v for vibrate, b for beep): ").strip().lower()

    if test_mode:
        print("Test mode activated.")
        while True:
            execute_action(action, intensity, duration)
            sleep(duration)
            repeat = input("Repeat the action? (y/n): ").strip().lower()
            if repeat != 'y':
                break
    else:
        time_until_alarm, alarm_time = calculate_time_until_alarm(alarm_time_str)

        if not loaded_from_file:
            save_alarm = input("Would you like to save this alarm settings for future use? (y/n): ").strip().lower()
            if save_alarm == 'y':
                save_alarm_settings(alarm_time_str, intensity, duration)
                print("Alarm settings saved.")

        print(f"Alarm is set for {alarm_time.strftime('%H:%M')}.")
        
        vibration_thread = Thread(target=periodic_vibration)
        vibration_thread.start()

        time_thread = Thread(target=check_for_time_left, args=(time_until_alarm,))
        time_thread.start()

        sleep(time_until_alarm)

        execute_action(action, intensity, duration)

        alarm_triggered = True
        vibration_thread.join(timeout=1)
        time_thread.join(timeout=1)

        if snooze_duration > 0:
            snooze = input("\nWould you like to snooze the alarm? (y/n): ").strip().lower()
            if snooze == 'y':
                snooze_alarm(action, intensity, duration)
            else:
                print("\nAlarm stopped.")
                print("\nExiting code now...")
                sys.exit()
        else:
            sys.exit()

if __name__ == "__main__":
    execute_shock()
