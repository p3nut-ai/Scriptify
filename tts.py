import base64
import requests
import threading

from typing import List
from termcolor import colored
from playsound import playsound

import time
from threading import Lock

lock = Lock()

VOICES = {
    "en_us_ghostface": "Ghost Face",
    "en_au_002": "English AU - Male",
    "en_uk_001": "English UK - Male 1",
    "en_us_010": "English US - Male 4",
    "en_male_narration": "English Male Narrator",
}

ENDPOINTS = [
    "https://tiktok-tts.weilnet.workers.dev/api/generation",
    "https://tiktoktts.com/api/tiktok-tts",
]
current_endpoint = 0
# in one conversion, the text can have a maximum length of 300 characters
TEXT_BYTE_LIMIT = 300


# create a list by splitting a string, every element has n chars
def split_string(string: str, chunk_size: int) -> List[str]:
    words = string.split()
    result = []
    current_chunk = ""
    for word in words:
        if (
            len(current_chunk) + len(word) + 1 <= chunk_size
        ):  # Check if adding the word exceeds the chunk size
            current_chunk += f" {word}"
        else:
            if current_chunk:  # Append the current chunk if not empty
                result.append(current_chunk.strip())
            current_chunk = word
    if current_chunk:  # Append the last chunk if not empty
        result.append(current_chunk.strip())
    return result


# checking if the website that provides the service is available
def get_api_response() -> requests.Response:
    url = f'{ENDPOINTS[current_endpoint].split("/a")[0]}'
    response = requests.get(url)
    return response


# saving the audio file
def save_audio_file(base64_data: str, filename: str = "output.mp3") -> None:
    audio_bytes = base64.b64decode(base64_data)
    with open(filename, "wb") as file:
        file.write(audio_bytes)


# send POST request to get the audio data
def generate_audio(text: str, voice: str) -> bytes:
    url = f"{ENDPOINTS[current_endpoint]}"
    headers = {"Content-Type": "application/json"}
    data = {"text": text, "voice": voice}
    response = requests.post(url, headers=headers, json=data)
    return response.content


# creates an text to speech audio file
def tts(
    text: str,
    voice: str = "none",
    filename: str = "output.mp3",
    play_sound: bool = False,
) -> None:
    # checking if the website is available
    global current_endpoint

    if get_api_response().status_code == 200:
        print(colored("[+] TikTok TTS Service available!", "green"))
    else:
        current_endpoint = (current_endpoint + 1) % 2
        if get_api_response().status_code == 200:
            print(colored("[+] TTS Service available!", "green"))
        else:
            print(colored("[-] TTS Service not available and probably temporarily rate limited, try again later..." , "red"))
            return

    # checking if arguments are valid
    if voice == "none":
        print(colored("[-] Please specify a voice", "red"))
        return

    if voice not in VOICES:
        print(colored("[-] Voice not available", "red"))
        return

    if not text:
        print(colored("[-] Please specify a text", "red"))
        return

    # creating the audio file
    try:
        if len(text) < TEXT_BYTE_LIMIT:
            audio = generate_audio((text), voice)
            if current_endpoint == 0:
                audio_base64_data = str(audio).split('"')[5]
            else:
                audio_base64_data = str(audio).split('"')[3].split(",")[1]

            if audio_base64_data == "error":
                print(colored("[-] This voice is unavailable right now", "red"))
                return

        else:
            # Split longer text into smaller parts
            text_parts = split_string(text, 299)
            audio_base64_data = [None] * len(text_parts)

            # Define a thread function to generate audio for each text part
            def generate_audio_thread(text_part, index, retries=3):
                for attempt in range(retries):
                    try:
                        audio = generate_audio(text_part, voice)
                        if current_endpoint == 0:
                            base64_data = str(audio).split('"')[5]
                        else:
                            base64_data = str(audio).split('"')[3].split(",")[1]

                        if base64_data == "error":
                            raise ValueError("This voice is unavailable right now")

                        with lock:
                            audio_base64_data[index] = base64_data
                        return
                    except Exception as e:
                        print(colored(f"Thread {index} failed on attempt {attempt + 1}: {e}", "red"))
                        time.sleep(1)

                with lock:
                    audio_base64_data[index] = ""
                print(colored(f"Thread {index} failed after {retries} attempts.", "red"))

            threads = []
            for index, text_part in enumerate(text_parts):
                # Create and start a new thread for each text part
                thread = threading.Thread(
                    target=generate_audio_thread, args=(text_part, index)
                )
                thread.start()
                threads.append(thread)

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Concatenate the base64 data in the correct order
            audio_base64_data = "".join(audio_base64_data)

        save_audio_file(audio_base64_data, filename)
        print(colored(f"[+] Audio file saved successfully as '{filename}'", "green"))
        if play_sound:
            playsound(filename)

    except Exception as e:
        print(colored(f"[-] An error occurred during TTS: {e}", "red"))
