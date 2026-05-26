from threading import Thread
from collections import defaultdict
import cv2
from ultralytics import YOLO
import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

VIDEOS_DIR = Path(__file__).parent / "videos"
VIDEOS_DIR.mkdir(exist_ok=True)

model = YOLO("best.pt")

app = FastAPI(title="Salamander Tracker POC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount the videos folder over HTTP
app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")

job = {"status": "idle"}

@app.get("/")
def root():
    return {"ok": True}


def run_track_job():
    try:
        input_path = VIDEOS_DIR / "input.mp4"
        cap = cv2.VideoCapture(str(input_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"fps={fps} dims={width}x{height} frames={total}")

        # Delete old output file if it exists
        output_path = VIDEOS_DIR / "output.mp4"
        if output_path.exists():
            output_path.unlink()

        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*"avc1"),
            fps,
            (width, height),
        )

        # Check writer opened successfully
        if not writer.isOpened():
            raise RuntimeError("VideoWriter failed to open output file")

        frames_seen = defaultdict(int)
        label_for = {}
        last_pos = {}
        total_distance = defaultdict(float)


        for frame_idx in range(total):
            ok, frame = cap.read()
            if not ok:
                break
            result = model.track(frame, persist=True, verbose=False)[0]
            writer.write(result.plot(labels=True))

            boxes = result.boxes
            if boxes is not None and boxes.id is not None:
                for tid, cls_id, box in zip(boxes.id.tolist(), boxes.cls.tolist(), boxes.xyxy.tolist()):
                    frames_seen[int(tid)] += 1
                    label_for[int(tid)] = model.names[int(cls_id)]  # use model names

                    # calculate center of bounding box
                    cx = (box[0] + box[2]) / 2
                    cy = (box[1] + box[3]) / 2

                    # add distance from last position
                    if tid in last_pos:
                        px, py = last_pos[tid]
                        total_distance[tid] += ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5
                    
                    last_pos[tid] = (cx, cy)
            job["percent"] = int((frame_idx + 1) / total * 100)
            if frame_idx % 30 == 0:
                print(f"frame {frame_idx}/{total}")

        cap.release()
        writer.release()

        tracks = [
            {
                "track_id": tid,
                "time_on_screen_s": round(count / fps, 2),
                "label": label_for.get(tid, "unknown"),  # safe fallback
                "distance_px": round(total_distance[tid], 1),
            }
            for tid, count in frames_seen.items()
        ]

        job.clear()
        job["status"] = "done"
        job["percent"] = 100
        job["result"] = {
            "video_url": f"http://localhost:8000/videos/output.mp4?t={int(time.time())}",
            "tracks": tracks,
        }

    except Exception as e:
        print(f"error: {e}", flush=True)
        job.clear()
        job["status"] = "error"
        job["message"] = str(e)


# upload + process endpoint
@app.post("/track")
def start_track(video: UploadFile = File(...)):
    (VIDEOS_DIR / "input.mp4").write_bytes(video.file.read())
    job.clear()
    job["status"] = "processing"
    job["percent"] = 0
    Thread(target=run_track_job, daemon=True).start()
    return {"status": "processing"}

@app.get("/track")
def get_track():
    return job

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)