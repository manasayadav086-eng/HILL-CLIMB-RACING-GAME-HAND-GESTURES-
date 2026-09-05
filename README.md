# Game Automation

A Windows webcam-based game controller that uses hand gestures to press keyboard keys for braking and accelerating.

## How It Works

`main.py` uses MediaPipe Hand Landmarker to detect one hand from the webcam:

| Gesture | Detected fingers | Action |
| --- | ---: | --- |
| Brake | 0 or 1 | Presses the left/brake key (`K`) |
| Gas | 3 or 4 | Presses the right/gas key (`M`) |
| Neutral | 2 | Releases both keys |
| No hand | No hand detected | Releases both keys |

The camera preview is mirrored and shows the current gesture. The program waits for three consistent frames before changing the active gesture, which helps reduce accidental key presses.

## Requirements

- Windows
- Python 3.9 or newer
- A working webcam
- A game that accepts `K` for brake and `M` for gas, or matching key bindings configured in `directkeys.py`

Install the Python dependencies:

```powershell
python -m pip install opencv-python mediapipe
```

## Run

From the project folder, run:

```powershell
python main.py
```

The first run downloads `hand_landmarker.task` automatically if it is not already in the project folder. Allow webcam access when Windows asks for permission.

To stop the program, focus the camera window and press `Q`. Any held key is released when the program exits.

## Files

- `main.py` - Webcam capture, hand tracking, gesture detection, and game control.
- `directkeys.py` - Windows keyboard input helpers using `SendInput`.
- `hand_landmarker.task` - MediaPipe hand detection model. It can be downloaded automatically by `main.py`.
- `step.txt` - Older/incomplete experiment code; it is not required to run the current program.

## Troubleshooting

### Webcam cannot be opened

Check that the webcam is connected, close other applications using it, and verify that Python has camera permission in Windows Settings.

### The game does not respond

Start the game and make sure its window is focused. Confirm that its brake and accelerator controls use `K` and `M`, or update `left_pressed` and `right_pressed` in `directkeys.py`.

### Gestures are detected unreliably

Use good lighting, keep your hand inside the yellow guide box, and keep the hand visible at a comfortable distance from the camera.

## Safety

Test the controller in a safe environment. This project sends keyboard input to the focused Windows application and can control any application that has matching key bindings.