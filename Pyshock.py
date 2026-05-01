import requests
import json
from typing import Dict, Tuple
from threading import Thread

# Constants
PISHOCK_URL = "https://api.pishock.com/Shockers/"

# Error messages
ERROR_MESSAGES = {
    "This code doesn't exist.": "The specified share code could not be found. Make sure you create and copy an active share code from the PiShock website.",
    "Not Authorized.": "The specified username or apikey is not correct (or your account has not been activated).",
    "Shocker is Paused, unable to send command.": "The shocker is paused (from the PiShock.com web panel).",
    "Device currently not connected.": "The PiShock is offline.",
    "This share code has already been used by somebody else.": "Someone (or something) else is using the specified share code. Generate a new one.",
    "Unknown Op, use 0 for shock, 1 for vibrate and 2 for beep.": "Invalid Op code specified. Must be 0, 1, or 2.",
    "Intensity must be between 0 and 100": "The specified intensity was outside the permitted range.",
    "Duration must be between 0 and 15": "The specified duration was outside the permitted range."
}


class PishockAPI(object):
    def __init__(self, api_key: str, username: str, sharecode: list[str], app_name: str):
        self.api_key: str = api_key
        self.username: str = username
        self.app_name: str = app_name
        self.sharecode: list[str] = sharecode 
        self.base_url: str = PISHOCK_URL
        self.headers: Dict[str, str] = {
            "accept": "*/*",
            "X-PiShock-Api-Key": self.api_key,
            "X-PiShock-Username": self.username,
            "Content-Type": "application/json",
        }

    def _check_response(self, response: requests.Response) -> None:
        """Check if a response from the server is valid.
        If the response is not valid, raise an exception."""
        if response.status_code != 204:
            raise ValueError(f"Invalid response from server: {response.text}")
        if response.text == "Operation Succeeded.":
            return
        if response.text in ERROR_MESSAGES:
            raise ValueError(ERROR_MESSAGES[response.text])

    def _send_request(self, code, data: Dict[str, str]) -> None:
        """Send a request to the PiShock API."""
        response = requests.post(
            url=f"{self.base_url}{code}",
            headers=self.headers,
            data=json.dumps(data)
        )
        self._check_response(response)


    def sanity_check(self, intensity: int, duration: int) -> tuple[int, int]:
        """Shock the user with the specified intensity and duration.
            Intensity must be between 0 and 1, duration must be between 0 and 15 (or 500 for 0.5 seconds)."""
        if not 0 <= intensity <= 100:
            raise ValueError("Intensity must be between 1 and 100")
        if not 0 <= duration <= 15 and duration != 300:
            raise ValueError("Duration must be between 0 and 15")
        # Convert intensity to a percentage
        intensity = int(intensity)
        # Convert duration to ms
        duration = int(duration*1000)
        return intensity, duration


    def send_response(self, intensity: int, duration: int, operation: int) -> None:
        threads = []
        for code in self.sharecode:
            data = {
                "AgentName": self.app_name,
                "Operation": operation,
                "Duration": duration,
                "Intensity": intensity,
                "MinimumDuration": duration,
                "MinimumIntensity": intensity,
                "IntensityAsPercentage": True
            }
            t = Thread(target=self._send_request, args=(code, data,))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()


    def shock(self, intensity: int, duration: int) -> None:
        """Shock the user with the specified intensity and duration.
        Intensity must be between 0 and 1, duration must be between 0 and 15 (or 0.5 for 0.5 seconds)."""
        intensity, duration = self.sanity_check(intensity, duration)
        self.send_response(intensity, duration, operation=0)


    def minishock(self, intensity: float) -> None:
        """A shortcut for a 0.5 second shock at the specified intensity."""
        self.shock(intensity, 500)

    def vibrate(self, intensity: int, duration: int) -> None:
        """Vibrate the user with the specified intensity and duration.
        Intensity must be between 0 and 100, duration must be between 0 and 15."""
        intensity, duration = self.sanity_check(intensity, duration)
        self.send_response(intensity, duration, operation=1)


    def beep(self, duration: int) -> None:
        """Beep the user for the specified duration.
        Duration must be between 0 and 15."""
        _, duration = self.sanity_check(0, duration)
        self.send_response(0, duration, operation=2)
