# Whisper Transcription API - Network Server

Share your local Whisper transcription with other devices on your network!

## How It Works

```
Other Devices (Phone, Laptop, etc.)
    ↓ (Wi-Fi)
Your Mac: HTTP API Server → whisper.cpp
    ↓
Transcription returned as JSON
```

## Start the Server

On your Mac, run:
```bash
cd /Users/lungs/Developer/whisper-stack
./start-api-server.sh
```

The server will show you the URL to use from other devices.

## From Other Devices

### Transcribe an audio file:

```bash
# From any device on your network
curl -X POST http://YOUR_MAC_IP:5001/transcribe \
  -F "file=@recording.mp3" \
  -F "verbatim=true" \
  -F "language=auto"
```

### Using Python:
```python
import requests

url = "http://YOUR_MAC_IP:5001/transcribe"
with open("recording.mp3", "rb") as f:
    response = requests.post(url, files={"file": f})
    print(response.json()['transcript'])
```

### Using JavaScript/Fetch:
```javascript
const url = "http://YOUR_MAC_IP:5001/transcribe";
const formData = new FormData();
formData.append("file", audioFile);
formData.append("verbatim", "true");

const response = await fetch(url, { method: "POST", body: formData });
const result = await response.json();
console.log(result.transcript);
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/status` | GET | Check if service is ready |
| `/model` | GET | Model information |
| `/transcribe` | POST | Transcribe audio file |
| `/record` | POST | Record from Mac's microphone |

## Features

- ✅ **100% offline** — No data leaves your network
- ✅ **Mixed languages** — English + Chinese auto-detected
- ✅ **Verbatim mode** — Preserves stammers, pauses
- ✅ **No API fees** — Uses local model

## Security Note

This server has no authentication. Only use on trusted networks (home/office).
