"""Buscar el balon en el video tactico con un detector ya entrenado (de otros partidos).

El tracking automatico pierde el balon en ~41% de los frames que califican, entonces
aqui lo buscamos en el video solo en esos frames. El modelo es el de roboflow/sports
(football-ball-detection, YOLOv8, codigo MIT) entrenado con videos de la Bundesliga
(dataset DFL de kaggle). Nunca vio este partido. No entrenamos ni ajustamos nada con
el video ni con el ground truth, eso lo prohibe el correo de aclaracion de reglas.

Los settings de inferencia son los mismos que usa roboflow/sports para ese modelo
(tiles de 640, imgsz 640, nms 0.1). El conf lo dejamos bajito a proposito y guardamos
todos los candidatos con su score, la seleccion se hace despues.

Tambien corre en 1 de cada 25 frames donde el ATD si tiene balon. Eso es solo para
ver que tanto coinciden detector y tracking (check automatico), no para elegir umbrales.

Como correrlo (mac):
    pip install -r tools/requirements-video.txt
    python tools/ball_from_video.py --download-weights   # una vez
    python tools/ball_from_video.py --limit 300          # prueba, para ver los fps
    python tools/ball_from_video.py                      # todo, se puede cortar y reanudar

Sale en outputs/ball_video.csv (esta en el gitignore, no se puede publicar data
derivada del video frame por frame)

    frame,reason,rank,px,py,conf,pitch_x,pitch_y

reason = "missing" (el ATD no tenia balon) o "check". rank 0 = el mas seguro.
si no encontro nada se escribe una fila con rank -1 para saber que ya se proceso.
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

WEIGHTS_GDRIVE_ID = "1isw4wx-MK9h9LMr36VvIWlJD6ppUvw7V"   # sacado del setup.sh de roboflow/sports
DEFAULT_WEIGHTS = os.path.join(ROOT, "models", "football-ball-detection.pt")
DEFAULT_OUT = os.path.join(ROOT, "outputs", "ball_video.csv")

HALVES = ((11185, 90651), (110808, 190197))   # frames que califican (DATA.md)
TILE = 640                                     # tamaño de tile igual que roboflow
OVERLAP = 64                                   # px, para que no se corte el balon entre tiles
IMGSZ = 640
NMS_IOU = 0.1                                  # igual que roboflow
CONF_FLOOR = 0.05                              # guardamos hasta los debiles, se filtra despues
MAX_PER_FRAME = 5
PITCH_MARGIN = 0.03                            # un poquito fuera de la cancha todavia cuenta


def frames_to_process(atd_raw, check_every):
    # regresa {frame_video: reason}, solo lee la parte del balon de cada linea
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
    parser = argparse.ArgumentParser(description="detector de balon sobre el video tactico")
    parser.add_argument("--weights", default=DEFAULT_WEIGHTS)
    parser.add_argument("--video", default=None, help="por default el video tactico")
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--device", default="mps", help="mps en mac, cuda o cpu")
    parser.add_argument("--check-every", type=int, default=25,
                        help="correr tambien en 1 de cada N frames con balon en el ATD (0 = no)")
    parser.add_argument("--limit", type=int, default=0, help="parar despues de N frames (para probar)")
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
    print("frames: {} sin balon + {} check, {} ya hechos, faltan {}".format(
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
        sys.exit("no se pudo abrir el video: {}".format(video_path))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    origins = tile_origins(width, height)

    n_video = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    print("video {}x{}, {} frames (deberian ser 199319), {} tiles por frame".format(
        width, height, n_video, len(origins)))
    # siempre leemos desde el frame 0, sin hacer seek. el seek en mp4 a veces cae unos frames
    # despues y eso nos desalinea todo. con grab() saltar frames tarda poco
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
            # si dos tiles detectan lo mismo (a menos de 6px) nos quedamos con el de mas conf
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
                        continue          # esta en la grada o en un anuncio, fuera
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
                print("  {:>6}/{}  frame {:>6}  {:.1f} fps  faltan ~{:.0f} min".format(
                    processed, len(todo), position, rate, left), flush=True)
    except KeyboardInterrupt:
        print("\nse corto, pero lo avanzado ya esta guardado. correlo otra vez para seguir")
    finally:
        out.close()
        capture.release()
    print("listo {} ({} frames en esta corrida)".format(args.out, processed))


if __name__ == "__main__":
    main()
