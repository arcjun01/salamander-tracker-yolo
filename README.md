## Salamander Tracker

Upload a salamander video and get back an annotated video with bounding boxes and a metrics table.

# What the App Does

- Accepts a video upload
- Runs YOLO object tracking on each frame
- Writes an annotated output video
- Computes per-track statistics:
  - `Track ID`
  - `Label`
  - `Time on Screen (s)`
- Streams progress updates while processing

## Metrics Implemented

The app calculates the amount of time each detected track spends on screen by counting frames per track and converting to seconds using the video FPS.



## Architecture

- Backend: `backend/main.py`
  - Loads `best.pt` with the Ultralytics YOLO API
  - Accepts video uploads at `POST /track`
  - Runs tracking in a background thread
  - Reports progress via `GET /track`
  - Serves the processed output video at `/videos/output.mp4`
- Frontend: `frontend/src/App.jsx`
  - Upload form for video files
  - Displays async progress with a progress bar
  - Shows the output video when complete
  - Displays per-track metrics in a table

## How to run

### Backend
```bash
cd backend
python -m venv venv
source venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
The backend listens on `http://127.0.0.1:8000`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

## Training
- ~150 frames labeled using Label Studio

- Trained with Ultralytics YOLO
- Model file: `backend/best.pt`

## Metrics
- Time on Screen — how long each salamander was visible(S)
- Distance Traveled —  how far each salamander moved across the video

## Color Masking vs YOLO Comparison

Based on the tracking output, YOLO is more robust than color masking for salamander tracking because it can recognize object shape and context rather than relying only on pixel color.

- Example where YOLO succeeds and color masking struggles:
  - A salamander moving across a background with similar color tones or shadows. YOLO still detects the salamander by its learned object features, while color masking would often mistake the background for the animal or lose the subject entirely.
- Example where color masking could be just as good or better:
  - A very simple scene where the salamander appears on a high-contrast, uniform background and the animal has a distinctive color. In that case, a well-tuned color mask can isolate the salamander quickly and with low computation.

## Stack
- Backend: Python, FastAPI, OpenCV, Ultralytics YOLO
- Frontend: React, Vite






