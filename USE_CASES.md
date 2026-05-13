# 🚀 Use Cases & Agent Integrations

## Primary Use Cases

### 1. Interview Prep Agent
```
You speak → Agent transcribes → Agent analyzes → Feedback loop

Flow:
1. Record practice answer (30-60s)
2. Get verbatim transcript with stammers/fillers
3. Agent analyzes: clarity, confidence, content
4. Suggest improvements
5. Repeat with refined answers
```

**Example prompt:**
```
"Transcribe my practice interview answer and provide feedback on:
- Number of filler words (um, uh, like)
- Speaking clarity and pace
- Content quality and completeness
- Suggestions for improvement"
```

### 2. Meeting Notes Agent
```
Meeting recording → Structured summary → Action items

Flow:
1. Record entire meeting (30-60 min)
2. Transcribe with speaker diarization (future)
3. Extract key decisions
4. List action items with owners
5. Send summary email
```

### 3. Voice Journal / Diary
```
Daily voice entry → Transcribe → Store + optional analysis

Flow:
1. Record thoughts (2-5 min)
2. Transcribe automatically
3. Save to markdown file
4. Optional: Sentiment analysis over time
5. Searchable voice archive
```

### 4. Content Repurposing
```
Podcast/Video → Transcript → Blog post + Social clips

Flow:
1. Upload long-form audio
2. Get full transcript
3. Agent extracts key quotes
4. Generates shorter content
5. Creates social media posts
```

### 5. Language Learning Partner
```
You speak target language → Transcription + Correction

Flow:
1. Practice speaking Chinese/Spanish/etc
2. Get accurate transcription
3. Agent highlights grammar mistakes
4. Suggests better phrasing
5. Tracks progress over time
```

### 6. Code Review Voice Notes
```
Dev speaks notes → Transcript → GitHub comment

Flow:
1. Record code review thoughts
2. Transcribe immediately
3. Post to GitHub/PR as comment
4. Searchable voice history for context
```

### 7. Customer Support Agent
```
Customer call → Transcript → Sentiment → Action

Flow:
1. Record support call
2. Transcribe with timestamps
3. Detect customer sentiment
4. Classify issue type
5. Suggest resolution
6. Update ticket
```

---

## Agent Integration Examples

### Python / LangChain

```python
from langchain.tools import tool

@tool
def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file using whisper-stack"""
    import requests
    with open(audio_path, 'rb') as f:
        response = requests.post(
            'http://localhost:5001/v1/transcribe',
            files={'file': f},
            data={'verbatim': True}
        )
    return response.json()['transcript']
```

### AutoGPT / Agent Protocol

```json
{
  "tools": [
    {
      "name": "local_whisper_transcribe",
      "description": "Transcribe audio files with mixed language support",
      "endpoint": "http://localhost:5001/v1/transcribe",
      "method": "POST",
      "parameters": {
        "file": {"type": "file", "required": true},
        "language": {"type": "string", "default": "auto"},
        "verbatim": {"type": "boolean", "default": true}
      }
    }
  ]
}
```

### n8n / Node-RED

```javascript
// HTTP Request node
POST http://localhost:5001/v1/transcribe
Form Data:
- file: {{ $json.audioFile }}
- verbatim: true

// Parse response
{{ $json.transcript }}
{{ $json.word_count }} words
{{ $json.filler_words.um }} "um" counts
```

### OpenAI Function Calling

```python
import openai

functions = [
    {
        "name": "transcribe_audio",
        "description": "Transcribe audio file for analysis",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "verbatim": {"type": "boolean"}
            }
        }
    }
]
```

---

## CLI Toolchains

### Bash + Claude

```bash
# Record → Transcribe → Send to Claude
./record-and-transcribe.sh 60 | \
  claude "Analyze this transcript for interview feedback"
```

### Obsidian Integration

```bash
# Record → Transcribe → Add to daily note
./record-and-transcribe.sh 120 | \
  tee -a ~/Obsidian/Journal/$(date +%Y-%m-%d).md
```

### Notion Integration

```python
import requests

# Record → Transcribe → Add to Notion database
transcript = transcribe_audio("meeting.mp3")
notion.pages.create(parent={"database_id": ID}, properties={
    "Title": {"title": [{"text": transcript[:50]}]},
    "Transcript": {"rich_text": [{"text": transcript}]},
    "Date": {"date": {"start": "2024-01-01"}}
})
```

---

## Response Formats

### Standard JSON Response

```json
{
  "success": true,
  "transcript": "Full text here...",
  "language": "en",
  "duration_seconds": 45.2,
  "word_count": 187,
  "filler_words": {
    "um": 3,
    "uh": 1,
    "like": 2
  },
  "metadata": {
    "model": "large-v3-turbo",
    "timestamp": "2024-01-01T12:00:00",
    "verbatim": true
  }
}
```

### Verbatim Word-Level

```
[00:00:00.000 --> 00:00:01.500]  Hello,
[00:00:01.500 --> 00:00:02.300]  um,
[00:00:02.300 --> 00:00:04.000]  I think...
```

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Latency | ~2-3 seconds for 1 minute audio |
| Accuracy | ~95% on clear speech |
| Mixed EN/CN | Excellent code-switching detection |
| Max file size | 100MB |
| Concurrent requests | Limited by CPU (scales with cores) |

---

## Future Enhancements

- [ ] Speaker diarization (who spoke when)
- [ ] Sentiment analysis
- [ ] Keyword spotting
- [ ] Real-time streaming API
- [ ] WebSocket support
- [ ] Batch processing
- [ ] Docker image
