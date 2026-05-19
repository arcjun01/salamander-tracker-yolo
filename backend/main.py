import cv2
from ultralytics import YOLO
import time
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

VIDEOS_DIR = Path(__file__).parent / "videos"
VIDEOS_DIR.mkdir(exist_ok=True)

model = YOLO("best.pt")  # swap to "best.pt" after training

app = FastAPI(title="Salamander Tracker POC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount the videos folder over HTTP
app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")


@app.get("/")
def root():
    return {"ok": True}


# upload + process endpoint
@app.post("/track")
def start_track(video: UploadFile = File(...)):
    # Save upload to disk
    input_path = VIDEOS_DIR / "input.mp4"
    input_path.write_bytes(video.file.read())

    # Open video and read metadata
    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"fps={fps} dims={width}x{height} frames={total}")

    # Set up output writer
    output_path = VIDEOS_DIR / "output.mp4"
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"avc1"),
        fps,
        (width, height),
    )

    # Process every frame
    for frame_idx in range(total):
        ok, frame = cap.read()
        if not ok:
            break
        result = model.track(frame, persist=True, verbose=False)[0]
        writer.write(result.plot())
        if frame_idx % 30 == 0:
            print(f"frame {frame_idx}/{total}")

    cap.release()
    writer.release()

    return {
        "status": "done",
        "video_url": f"http://localhost:8000/videos/output.mp4?t={int(time.time())}",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)