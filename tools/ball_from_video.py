"""Detect the ball in the tactical video with a public, pre-trained detector.

Why this exists
---------------
The automatic tracking loses the ball on 41% of graded frames. This script looks for it in the
video on exactly those frames, with a model that was trained on OTHER games, and writes every
candidate it finds to a small CSV. Nothing here is trained, fitted or tuned on this match, its
video or its ground truth (see the organisers' rule clarification).

The detector
------------
roboflow/sports "football-ball-detection" (YOLOv8, MIT-licensed code), trained on the Roboflow
Universe dataset roboflow-jvuqo/football-ball-detection-rejhg, built from the DFL Bundesliga
Kaggle videos. Not LaLiga, not this match.

Inference settings are the ones roboflow/sports ships for that model (640 px tiles, imgsz 640,
NMS IoU 0.1). The confidence floor is deliberately low: every candidate is written out with its
score, and choosing among them happens later, offline, with rules calibrated on external data.

Which frames
------------
By default only graded frames (both halves) where the ATD has no ball, plus one frame in every
--check-every frames where the ATD does have it. That second set exists for an automatic check
only: how often detector and ATD agree. It is never used to pick thresholds.

Run (Apple Silicon)
-------------------
    pip install -r tools/requirements-video.txt
    python tools/ball_from_video.py --download-weights      # once
    python tools/ball_from_video.py                          # resumable; Ctrl-C is safe

Output: outputs/ball_video.csv  (gitignored -- frame-level data derived from the match video
must not be published, see RULES.md)

    frame,reason,rank,px,py,conf,pitch_x,pitch_y

`reason` is "missing" (ATD had no ball) or "check". `rank` 0 is the most confident candidate.
Frames with no candidate get one row with rank -1 so a resumed run knows they were processed.
"""

import argparse
import csv
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "starter"))
from games import asset_paths  # noqa: E402
from load_homography import load as load_homography, unproject  # noqa: E402

WEIGHTS_GDRIVE_ID = "1isw4wx-MK9h9LMr36VvIWlJD6ppUvw7V"   # from roboflow/sports setup.sh
DEFAULT_WEIGHTS = os.path.join(ROOT, "models", "football-ball-detection.pt")
DEFAULT_OUT = os.path.join(ROOT, "outputs", "ball_video.csv")

HALVES = ((11185, 90651), (110808, 190197))   # graded video frames, from DATA.md
TILE = 640                                     # roboflow/sports slice size
OVERLAP = 64                                   # px, so a ball on a tile seam is not cut in half
IMGSZ = 640
NMS_IOU = 0.1                                  # roboflow/sports value
CONF_FLOOR = 0.05                              # keep weak candidates; selection happens later
MAX_PER_FRAME = 5
PITCH_MARGIN = 0.03                            # normalised; tolerance outside the touchlines


def frames_to_process(atd_raw, check_every):
    """{video_frame: reason}. Reads only the ball field of each ATD line."""
    wanted = {}
    graded = np.zeros(200000, dtype=bool)
    for start, end in HALVES:
        graded[start:end + 1] = True
    with open(atd_raw) as handle:
        for line in handle:
            frame_id = int(line[:line.index(":")])
            video_frame = frame_id - 1
            if not graded[video_frame]:
                continue
            ball = line.rstrip().rsplit(":", 1)[1]
            if ball.startswith("N"):
                wanted[video_frame] = "missing"
            elif check_every and video_frame % check_every == 0:
                wanted[video_frame] = "check"
    return wanted


def tile_origins(width, height):
    def starts(size):
        step = TILE - OVERLAP
        out = list(range(0, max(size - TILE, 0) + 1, step))
        if out[-1] + TILE < size:
            out.append(size - TILE)
        return out
    return [(x, y) for y in starts(height) for x in starts(width)]


def already_done(path):
    done = set()
    if os.path.exists(path):
        with open(path) as handle:
            for row in csv.DictReader(handle):
                done.add(int(row["frame"]))
    return done


def download_weights(path):
    import gdown
    os.makedirs(os.path.dirname(path), exist_ok=True)
    gdown.download(id=WEIGHTS_GDRIVE_ID, output=path, quiet=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--weights", default=DEFAULT_WEIGHTS)
    parser.add_argument("--video", default=None, help="defaults to the tactical video")
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--device", default="mps", help="mps on Apple Silicon, cuda, or cpu")
    parser.add_argument("--check-every", type=int, default=25,
                        help="also run on 1 in N frames where the ATD has the ball (0 = never)")
    parser.add_argument("--limit", type=int, default=0, help="stop after N frames (smoke test)")
    parser.add_argument("--download-weights", action="store_true")
    args = parser.parse_args()

    if args.download_weights:
        download_weights(args.weights)
        return

    import cv2
    from ultralytics import YOLO

    paths = asset_paths()
    video_path = args.video or paths["video"]
    wanted = frames_to_process(paths["atd_raw"], args.check_every)
    done = already_done(args.out)
    todo = sorted(f for f in wanted if f not in done)
    if args.limit:
        todo = todo[:args.limit]
    n_missing = sum(1 for r in wanted.values() if r == "missing")
    print("frames: {} missing-ball + {} check, {} already done, {} to go".format(
        n_missing, len(wanted) - n_missing, len(done), len(todo)))
    if not todo:
        return

    H, _, valid = load_homography()
    model = YOLO(args.weights)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    new_file = not os.path.exists(args.out)
    out = open(args.out, "a", newline="")
    writer = csv.writer(out)
    if new_file:
        writer.writerow(["frame", "reason", "rank", "px", "py", "conf", "pitch_x", "pitch_y"])

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        sys.exit("cannot open video: {}".format(video_path))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    origins = tile_origins(width, height)

    n_video = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    print("video {}x{}, {} frames (expected 199319), {} tiles per frame".format(
        width, height, n_video, len(origins)))
    # Always read from frame 0, never seek: seeking in an mp4 can land a few frames off, and a
    # few frames off is a wrong answer here. Skipping with grab() costs minutes, not hours.
    position = 0

    todo_set = set(todo)
    last = todo[-1]
    processed, t0 = 0, time.time()
    try:
        while position <= last:
            if position not in todo_set:
                if not capture.grab():
                    break
                position += 1
                continue
            ok, frame = capture.read()
            if not ok:
                break
            tiles = [frame[y:y + TILE, x:x + TILE] for x, y in origins]
            results = model.predict(tiles, imgsz=IMGSZ, conf=CONF_FLOOR, iou=NMS_IOU,
                                    device=args.device, verbose=False)
            boxes = []
            for (ox, oy), result in zip(origins, results):
                for xyxy, conf in zip(result.boxes.xyxy.cpu().numpy(),
                                      result.boxes.conf.cpu().numpy()):
                    cx = (xyxy[0] + xyxy[2]) / 2 + ox
                    cy = (xyxy[1] + xyxy[3]) / 2 + oy
                    boxes.append((float(conf), float(cx), float(cy)))
            # merge duplicates from overlapping tiles: keep the stronger of two within 6 px
            boxes.sort(reverse=True)
            kept = []
            for conf, cx, cy in boxes:
                if all((cx - kx) ** 2 + (cy - ky) ** 2 > 36 for _, kx, ky in kept):
                    kept.append((conf, cx, cy))
            rows = []
            for conf, cx, cy in kept:
                if valid[position]:
                    gx, gy = unproject(H[position], cx, cy)
                    gx, gy = float(gx), float(gy)
                    if not (-PITCH_MARGIN <= gx <= 1 + PITCH_MARGIN
                            and -PITCH_MARGIN <= gy <= 1 + PITCH_MARGIN):
                        continue          # in the stands, on a sponsor board, etc.
                else:
                    gx = gy = float("nan")
                rows.append((conf, cx, cy, gx, gy))
                if len(rows) == MAX_PER_FRAME:
                    break
            reason = wanted[position]
            if rows:
                for rank, (conf, cx, cy, gx, gy) in enumerate(rows):
                    writer.writerow([position, reason, rank, round(cx, 1), round(cy, 1),
                                     round(conf, 4), round(gx, 5), round(gy, 5)])
            else:
                writer.writerow([position, reason, -1, "", "", "", "", ""])
            position += 1
            processed += 1
            if processed % 500 == 0:
                out.flush()
                rate = processed / (time.time() - t0)
                left = (len(todo) - processed) / rate / 60
                print("  {:>6}/{}  frame {:>6}  {:.1f} fps  ~{:.0f} min left".format(
                    processed, len(todo), position, rate, left), flush=True)
    except KeyboardInterrupt:
        print("\ninterrupted; progress is saved, run again to resume")
    finally:
        out.close()
        capture.release()
    print("wrote {} ({} frames this run)".format(args.out, processed))


if __name__ == "__main__":
    main()
