-- Global Hotkey Dictation for whisper-stack
-- Save this as an Automator Quick Action or use with Hammerspoon
--
-- NOTE: Update the path below to your whisper-stack location

on run
  set whisperPath to POSIX file "/Users/lungs/Developer/whisper-stack"
  -- Or use: set whisperPath to POSIX file (POSIX path of (path to home folder as string) & "projects/whisper-stack")

  set recordScript to POSIX path of whisperPath & "record-and-transcribe.sh 10"

  tell application "Terminal"
    activate
    do script recordScript in front window
  end tell

  -- Wait for recording to complete, then get transcript
  delay 12

  -- Get the last line from output (the transcript)
  tell application "Terminal"
    set transcriptContents to contents of front window
  end tell

  -- Paste into active application
  tell application "System Events"
    keystroke "v" using command down
  end tell
end run
