import io
import wave
import requests
import numpy as np
import sounddevice as sd
import sys

BOT_URL = "http://localhost:8000"
ACCOUNT_NUMBER = "LN001"
SAMPLE_RATE = 16000
DURATION_SECONDS = 5

def get_devices():
    """Get input and output device indices, falling back to defaults if needed."""
    try:
        default_in = sd.default.device[0]
        default_out = sd.default.device[1]
    except Exception:
        default_in = None
        default_out = None
    
    # Try using typical default device if not configured
    return default_in, default_out

def record_audio(filename: str, input_device):
    print(f"\n[Recording] Speaking for {DURATION_SECONDS} seconds... (Speak now!)")
    try:
        recording = sd.rec(
            int(DURATION_SECONDS * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            device=input_device
        )
        sd.wait()
        with wave.open(filename, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(recording.tobytes())
        print("[Recording finished]")
    except Exception as e:
        print(f"Error recording audio: {e}")
        sys.exit(1)

def play_audio(filename: str, output_device):
    try:
        with wave.open(filename, "rb") as wav_file:
            data = wav_file.readframes(wav_file.getnframes())
            audio = np.frombuffer(data, dtype="int16")
            sd.play(audio, samplerate=wav_file.getframerate(), device=output_device)
            sd.wait()
    except Exception as e:
        print(f"Error playing audio: {e}")

def main():
    print("=" * 60)
    print("Debt Collections Voice Bot - Voice Client Simulator")
    print("=" * 60)
    
    account_num = input(f"Enter account number to call (default: {ACCOUNT_NUMBER}): ").strip()
    if not account_num:
        account_num = ACCOUNT_NUMBER

    input_device, output_device = get_devices()
    print(f"Using Audio Input Device: {input_device}")
    print(f"Using Audio Output Device: {output_device}")

    recorded_file = "recorded.wav"
    response_file = "response.wav"

    # Start Call
    print(f"\nCalling /call/start for account {account_num}...")
    try:
        start_resp = requests.post(f"{BOT_URL}/call/start?account_number={account_num}")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to FastAPI server at {BOT_URL}. Is it running?")
        return

    if start_resp.status_code != 200:
        print(f"Failed to start call. Status: {start_resp.status_code}, Detail: {start_resp.text}")
        return

    # Play Greeting
    print("Call connected. Playing greeting...")
    with open(response_file, "wb") as out:
        out.write(start_resp.content)
    play_audio(response_file, output_device)

    # Conversation Loop
    while True:
        print("\nOptions:")
        print("  [Enter] - Speak response (will record for 5 seconds)")
        print("  q       - Hang up / end call")
        user_choice = input("Your choice: ").strip().lower()

        if user_choice == 'q':
            print("Hanging up...")
            break

        # Record audio
        record_audio(recorded_file, input_device)

        # Send audio message
        print("Sending audio to bot...")
        try:
            with open(recorded_file, "rb") as f:
                files = {"file": (recorded_file, f, "audio/wav")}
                resp = requests.post(f"{BOT_URL}/call/message?account_number={account_num}", files=files)
        except Exception as e:
            print(f"Error communicating with bot server: {e}")
            break

        if resp.status_code != 200:
            print(f"Bot returned error: {resp.status_code}, {resp.text}")
            break

        with open(response_file, "wb") as out:
            out.write(resp.content)
        
        print("Playing bot response...")
        play_audio(response_file, output_device)

    # End Call
    print("\nCalling /call/end to log call outcome...")
    try:
        end_resp = requests.post(f"{BOT_URL}/call/end?account_number={account_num}")
        if end_resp.status_code == 200:
            result = end_resp.json()
            print(f"Call finalized with Status: {result.get('status')}")
            print(f"PTP Captured: {result.get('ptp_captured')}")
            print(f"Escalated: {result.get('escalated')}")
        else:
            print(f"Failed to end call properly: {end_resp.status_code}, {end_resp.text}")
    except Exception as e:
        print(f"Error ending call: {e}")

    print("\nCall session ended. Goodbye!")

if __name__ == "__main__":
    main()
