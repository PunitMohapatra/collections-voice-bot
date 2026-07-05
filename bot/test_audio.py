import sounddevice as sd

print("Available audio devices:")
for idx, device in enumerate(sd.query_devices()):
    print(f"{idx}: {device['name']} ({device['max_input_channels']} in, {device['max_output_channels']} out)")

print(f"Default input device: {sd.default.device[0]}")
print(f"Default output device: {sd.default.device[1]}")
