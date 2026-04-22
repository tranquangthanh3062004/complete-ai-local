# accident_monitor_gui.py
"""
Single-file Traffic Accident Detection GUI (PySimpleGUI)
- Supports: video file or webcam, local HF DETR model or download from HF
- Features: ROI selection (OpenCV), threshold, zoom, inference freq, pre/post buffer, save evidence clips,
            manual record, snapshot, save annotated output, counters, alerts list, export counts.
"""
import os
import time
import threading
import csv
from pathlib import Path
from collections import deque, OrderedDict

import cv2
import numpy as np
from PIL import Image
import base64
import io

# ...existing code...
import sys
import subprocess

try:
    import PySimpleGUI as sg
except ImportError:
    # Try to install automatically and retry import
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PySimpleGUI"])
        import PySimpleGUI as sg
    except Exception:
        print("Missing dependency: PySimpleGUI. Install manually with:")
        print(f"  {sys.executable} -m pip install PySimpleGUI")
        raise
# ...existing code...
# ML libs (transformers)
import torch
from transformers import AutoImageProcessor, DetrForObjectDetection
from huggingface_hub import snapshot_download

# -------------------- Config defaults --------------------
DEFAULT_HF_ID = "hilmantm/detr-traffic-accident-detection"
DEFAULT_MODEL_DIR = str(Path.home() / "detr_accident_model")
ALERTS_DIR = "alerts"
UPLOADS_DIR = "uploads"
os.makedirs(ALERTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# -------------------- Helper classes & functions --------------------
class CentroidTracker:
    def __init__(self, max_disappeared=10, max_distance=80):
        self.nextObjectID = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
    def register(self, centroid):
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.nextObjectID += 1
    def deregister(self, oid):
        if oid in self.objects: del self.objects[oid]
        if oid in self.disappeared: del self.disappeared[oid]
    def update(self, inputCentroids):
        if len(inputCentroids) == 0:
            for oid in list(self.disappeared.keys()):
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    self.deregister(oid)
            return self.objects
        if len(self.objects) == 0:
            for c in inputCentroids: self.register(c)
            return self.objects
        objectIDs = list(self.objects.keys())
        objectCentroids = list(self.objects.values())
        D = np.linalg.norm(np.array(objectCentroids)[:, None] - np.array(inputCentroids)[None, :], axis=2)
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]
        usedRows, usedCols = set(), set()
        for r,c in zip(rows, cols):
            if r in usedRows or c in usedCols: continue
            if D[r,c] > self.max_distance: continue
            oid = objectIDs[r]
            self.objects[oid] = inputCentroids[c]
            self.disappeared[oid] = 0
            usedRows.add(r); usedCols.add(c)
        for r in range(len(objectCentroids)):
            if r not in usedRows:
                oid = objectIDs[r]; self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared: self.deregister(oid)
        for c in range(len(inputCentroids)):
            if c not in usedCols: self.register(inputCentroids[c])
        return self.objects

def ensure_model_snapshot(local_dir, hf_id):
    p = Path(local_dir)
    if (p/"preprocessor_config.json").exists() and (p/"config.json").exists() and any((p/n).exists() for n in ("model.safetensors","pytorch_model.bin","pytorch_model.safetensors")):
        return str(p)
    # download snapshot
    sg.popup_non_blocking("Model not found locally. Downloading from Hugging Face (may take time)...", title="Downloading")
    local = snapshot_download(repo_id=hf_id, local_dir=local_dir, force_download=False)
    return local

def load_processor_and_model(path_or_id, use_hf=False):
    try:
        if use_hf:
            proc = AutoImageProcessor.from_pretrained(path_or_id)
            model = DetrForObjectDetection.from_pretrained(path_or_id)
        else:
            p = Path(path_or_id)
            if not (p/"preprocessor_config.json").exists():
                p = Path(ensure_model_snapshot(path_or_id, DEFAULT_HF_ID))
            proc = AutoImageProcessor.from_pretrained(str(p))
            model = DetrForObjectDetection.from_pretrained(str(p))
    except Exception as e:
        raise RuntimeError(f"Model load failed: {e}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    return proc, model, device

def bgr2pngbytes(frame):
    # convert BGR to PNG bytes
    _, buf = cv2.imencode(".png", frame)
    return buf.tobytes()

def save_clip(frames, filename, fps):
    if len(frames) == 0:
        return False
    h,w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(filename, fourcc, max(1.0, fps), (w,h))
    for f in frames: writer.write(f)
    writer.release()
    return True

def choose_roi_with_opencv(first_frame):
    """
    OpenCV interactive ROI setter.
    Drag to draw rectangle and press Enter/Space to confirm, Esc to cancel.
    Returns normalized roi (rx,ry,rw,rh) or None.
    """
    clone = first_frame.copy()
    roi = None
    rect = [0,0,0,0]
    drawing = False

    def mouse_cb(event, x, y, flags, param):
        nonlocal drawing, rect
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            rect[0], rect[1], rect[2], rect[3] = x, y, x, y
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            rect[2], rect[3] = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            rect[2], rect[3] = x, y

    win = "Select ROI - drag and release. ENTER to confirm, ESC to cancel"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win, mouse_cb)
    while True:
        vis = clone.copy()
        if rect[2] != 0 or rect[3] != 0:
            x1 = min(rect[0], rect[2]); y1 = min(rect[1], rect[3])
            x2 = max(rect[0], rect[2]); y2 = max(rect[1], rect[3])
            cv2.rectangle(vis, (x1,y1), (x2,y2), (0,255,255), 2)
        cv2.imshow(win, vis)
        k = cv2.waitKey(20) & 0xFF
        if k == 13 or k == 32:  # Enter or Space -> confirm
            if rect[2] == 0 and rect[3] == 0:
                roi = None
            else:
                x1 = min(rect[0], rect[2]); y1 = min(rect[1], rect[3])
                x2 = max(rect[0], rect[2]); y2 = max(rect[1], rect[3])
                h,w = clone.shape[:2]
                rw = max(1, x2-x1); rh = max(1, y2-y1)
                roi = (x1/w, y1/h, rw/w, rh/h)
            break
        if k == 27:  # Esc cancel
            roi = None
            break
    cv2.destroyWindow(win)
    return roi

# -------------------- GUI layout --------------------
sg.theme("DarkBlue3")
layout = [
    [sg.Text("Traffic Accident Detection — Local GUI", font=("Any", 14))],
    [
        sg.Column([
            [sg.Image(filename="", key="-IMAGE-", size=(960,540))],
            [sg.Text("Live FPS:"), sg.Text("0", key="-FPS-"), sg.Text(" | Status:"), sg.Text("Idle", key="-STATUS-")]
        ]),
        sg.Column([
            [sg.Frame("Source / Model", [
                [sg.Text("Video (file path or 0=webcam):"), sg.Input(key="-SOURCE-", size=(30,1)), sg.FileBrowse(file_types=(("Video Files","*.mp4;*.avi;*.mov;*.mkv"),), target="-SOURCE-")],
                [sg.Text("Model folder (local) or HF id:"), sg.Input(DEFAULT_MODEL_DIR, key="-MODEL-"), sg.Button("Browse Model")],
                [sg.Checkbox("Load from HF model id (use internet)", key="-USEHF-"), sg.Button("Download HF Model")],
                [sg.Button("Load Model", key="-LOADMODEL-"), sg.Text("", key="-MODELSTATUS-")]
            ])],
            [sg.Frame("Controls", [
                [sg.Button("Start", key="-START-"), sg.Button("Pause/Resume", key="-PAUSE-"), sg.Button("Stop", key="-STOP-")],
                [sg.Button("Set ROI (OpenCV)", key="-SETROI-"), sg.Button("Clear ROI", key="-CLEARROI-")],
                [sg.Button("Snapshot", key="-SNAP-"), sg.Button("Manual Record", key="-RECORD-"), sg.Button("Save Annotated", key="-SAVEOUT-")],
                [sg.Text("Threshold:"), sg.Slider(range=(0,100), orientation="h", default_value=50, key="-THR-")],
                [sg.Text("Infer every N frames:"), sg.Input("3", size=(5,1), key="-INFER-")],
                [sg.Text("Zoom x100:"), sg.Slider(range=(100,300), orientation="h", default_value=100, key="-ZOOM-")]
            ])],
            [sg.Frame("Counts / Alerts", [
                [sg.Multiline("", size=(40,6), key="-COUNTS-", disabled=True)],
                [sg.Text("Alerts saved:"), sg.Listbox(values=[], size=(40,6), key="-ALERTS-")],
                [sg.Button("Refresh Alerts", key="-REFRESHALERTS-"), sg.Button("Export counts CSV", key="-EXPORTCSV-")]
            ])],
            [sg.Frame("Logs", [[sg.Multiline("", size=(80,6), key="-LOG-", disabled=True)]])]
        ])
    ]
]

window = sg.Window("Accident Monitor", layout, finalize=True, location=(30,30))

# -------------------- Shared state --------------------
model_processor = None
model = None
device = None
worker_thread = None
worker_stop = threading.Event()
pause_flag = threading.Event()
manual_recording = False
manual_writer = None

# runtime variables (used by worker)
worker_state = {
    "source": "0",
    "threshold": 0.5,
    "infer_every": 3,
    "zoom": 1.0,
    "roi": None,
    "pre_seconds": 3.0,
    "post_seconds": 3.0,
    "save_annotated": None  # path to save annotated output
}

# -------------------- Worker function --------------------
def video_worker_thread(window, state):
    global model_processor, model, device, manual_writer, manual_recording
    try:
        src = state["source"]
        try:
            src_val = int(src) if str(src).isdigit() else src
        except:
            src_val = src
        cap = cv2.VideoCapture(src_val)
        if not cap.isOpened():
            window.write_event_value("-WORKER-LOG-", f"[ERROR] Cannot open source: {src}")
            return
        fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
        prebuf = deque(maxlen = max(1, int(state["pre_seconds"] * fps)))
        frame_idx = 0
        tracker = CentroidTracker(max_disappeared=8, max_distance=80)
        counts = {}
        seen_ids = set()
        annotated_out = None
        if state["save_annotated"]:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            # will create writer when we have first frame size
        last_time = time.time()
        window.write_event_value("-WORKER-LOG-", "[INFO] Starting processing...")
        while not worker_stop.is_set():
            if pause_flag.is_set():
                time.sleep(0.1)
                continue
            ret, frame = cap.read()
            if not ret:
                window.write_event_value("-WORKER-LOG-", "[INFO] End of stream.")
                break
            frame_idx += 1
            # apply zoom
            z = state.get("zoom", 1.0)
            if z != 1.0:
                h,w = frame.shape[:2]
                new_w = int(w / z); new_h = int(h / z); cx,cy = w//2, h//2
                x1 = max(0, cx-new_w//2); y1 = max(0, cy-new_h//2)
                x2 = min(w, x1+new_w); y2 = min(h, y1+new_h)
                crop = frame[y1:y2, x1:x2]; frame = cv2.resize(crop, (w,h))
            prebuf.append(frame.copy())
            boxes, labels, scores = [], [], []
            if frame_idx % max(1, state["infer_every"]) == 0:
                # inference
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil = Image.fromarray(rgb)
                    inputs = model_processor(images=pil, return_tensors="pt").to(device)
                    with torch.no_grad():
                        outputs = model(**inputs)
                    target_sizes = torch.tensor([pil.size[::-1]]).to(device)
                    results = model_processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=state["threshold"])[0]
                    for s, lbl, box in zip(results["scores"], results["labels"], results["boxes"]):
                        sc = float(s)
                        if sc < state["threshold"]: continue
                        x1,y1,x2,y2 = [int(v) for v in box.tolist()]
                        name = model.config.id2label.get(int(lbl.item()), str(int(lbl.item())))
                        boxes.append([x1,y1,x2,y2]); labels.append(name); scores.append(sc)
                except Exception as e:
                    window.write_event_value("-WORKER-LOG-", f"[WARN] Inference error: {e}")
            # tracking
            centroids = [(b[0] + (b[2]-b[0])//2, b[1] + (b[3]-b[1])//2) for b in boxes]
            objects = tracker.update(centroids)
            id_to_label = {}
            for oid, cent in objects.items():
                if len(centroids) == 0:
                    id_to_label[oid] = None; continue
                dists = [np.hypot(cent[0]-c[0], cent[1]-c[1]) for c in centroids]
                idx = int(np.argmin(dists))
                if dists[idx] < 100: id_to_label[oid] = labels[idx]
                else: id_to_label[oid] = None
            # counting in ROI
            frame_h, frame_w = frame.shape[:2]
            roi = state["roi"]
            for oid, cent in objects.items():
                lab = id_to_label.get(oid)
                if lab is None: continue
                if any(k in lab.lower() for k in ("car","truck","bus","motor","bicycle")):
                    if roi:
                        rx,ry,rw,rh = roi
                        rx_px = int(rx*frame_w); ry_px = int(ry*frame_h)
                        rw_px = int(rw*frame_w); rh_px = int(rh*frame_h)
                        if rx_px <= cent[0] <= rx_px+rw_px and ry_px <= cent[1] <= ry_px+rh_px:
                            if oid not in seen_ids:
                                counts[lab] = counts.get(lab, 0) + 1
                                seen_ids.add(oid)
            # draw boxes & labels
            for i, b in enumerate(boxes):
                x1,y1,x2,y2 = b
                cls = labels[i]; sc = scores[i]
                col = (0,255,0)
                if any(k in cls.lower() for k in ("accident","crash","collision")):
                    col = (0,0,255)
                cv2.rectangle(frame, (x1,y1),(x2,y2), col, 2)
                cv2.putText(frame, f"{cls} {sc:.2f}", (x1, max(12,y1-6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
            for oid, cent in objects.items():
                cv2.putText(frame, f"ID{oid}", (cent[0]-10, cent[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)
            # draw ROI if any
            if roi:
                rx,ry,rw,rh = roi
                x = int(rx*frame_w); y=int(ry*frame_h); w=int(rw*frame_w); h=int(rh*frame_h)
                cv2.rectangle(frame, (x,y),(x+w,y+h), (255,255,0), 2)
                cv2.putText(frame, "ROI", (x, max(12,y-6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)
            # accident detection -> overlay flash, save evidence
            accident_present = any(any(k in l.lower() for k in ("accident","crash","collision")) for l in labels)
            if accident_present:
                overlay = frame.copy()
                overlay[:] = (0,0,255)
                alpha = 0.35
                frame = cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0)
                # save clip (pre + post)
                ts = time.strftime("%Y%m%d_%H%M%S")
                outname = os.path.join(ALERTS_DIR, f"evidence_{ts}.mp4")
                frames_to_save = list(prebuf)
                post_n = int(state["post_seconds"] * fps)
                extra = []
                for _ in range(post_n):
                    r2, f2 = cap.read()
                    if not r2: break
                    extra.append(f2)
                frames_to_save.extend(extra)
                ok = save_clip(frames_to_save, outname, fps)
                if ok:
                    window.write_event_value("-ALERT-SAVED-", outname)
                    window.write_event_value("-WORKER-LOG-", f"[ALERT] Evidence saved: {outname}")
            # overlay counts
            if counts:
                y0 = 20
                for k,v in counts.items():
                    cv2.putText(frame, f"{k}: {v}", (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
                    y0 += 24
            # manual record
            if manual_recording:
                if manual_writer is None:
                    fname = os.path.join(ALERTS_DIR, f"manual_{time.strftime('%Y%m%d_%H%M%S')}.mp4")
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    manual_writer = cv2.VideoWriter(fname, fourcc, max(1.0, fps), (frame.shape[1], frame.shape[0]))
                    window.write_event_value("-WORKER-LOG-", f"[INFO] Manual record started: {fname}")
                if manual_writer:
                    manual_writer.write(frame)
            # write annotated frame to output writer if requested
            if state["save_annotated"]:
                if annotated_out is None:
                    annotated_out = cv2.VideoWriter(state["save_annotated"], cv2.VideoWriter_fourcc(*"mp4v"), max(1.0,fps), (frame.shape[1], frame.shape[0]))
                annotated_out.write(frame)
            # send frame to GUI
            try:
                imgbytes = bgr2pngbytes(frame)
                window.write_event_value("-FRAME-", imgbytes)
                window.write_event_value("-COUNTS-", counts.copy())
                # update FPS
                now = time.time()
                fps_real = 1.0 / (now - last_time) if now - last_time > 0 else 0.0
                last_time = now
                window.write_event_value("-FPS-", f"{fps_real:.1f}")
            except Exception as e:
                window.write_event_value("-WORKER-LOG-", f"[WARN] Frame transfer failed: {e}")
            # small sleep to be gentle
            time.sleep(0.001)
        # cleanup
        cap.release()
        if annotated_out:
            annotated_out.release()
        if manual_writer:
            manual_writer.release()
            manual_writer = None
        window.write_event_value("-WORKER-LOG-", "[INFO] Worker stopped.")
    except Exception as e:
        window.write_event_value("-WORKER-LOG-", f"[ERROR] Worker exception: {e}")

# -------------------- GUI event loop --------------------
def refresh_alerts_list():
    files = sorted([p.name for p in Path(ALERTS_DIR).glob("*.mp4")], reverse=True)
    window["-ALERTS-"].update(files)

def append_log(msg):
    prev = window["-LOG-"].get()
    t = time.strftime("%Y-%m-%d %H:%M:%S")
    window["-LOG-"].update(prev + f"{t} — {msg}\n")

refresh_alerts_list()
append_log("Ready.")

while True:
    event, values = window.read(timeout=100)
    if event == sg.WIN_CLOSED:
        # stop worker if running
        worker_stop.set()
        break
    if event == "-LOADMODEL-":
        # load model on click (blocking, heavy). Use try/except
        model_path = values["-MODEL-"].strip()
        usehf = values["-USEHF-"]
        try:
            append_log("Loading model (this may take time)...")
            model_processor, model, device = load_processor_and_model(model_path if model_path else DEFAULT_HF_ID, use_hf=usehf)
            append_log(f"Model loaded on device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
            window["-MODELSTATUS-"].update("Loaded")
        except Exception as e:
            append_log(f"Model load failed: {e}")
            window["-MODELSTATUS-"].update("Failed")
    if event == "-Download HF Model-":
        # not used (left for future)
        pass
    if event == "-SETROI-":
        # open first frame for ROI selection
        src = values["-SOURCE-"].strip() or "0"
        try:
            src_val = int(src) if str(src).isdigit() else src
        except:
            src_val = src
        cap_temp = cv2.VideoCapture(src_val)
        ok, f0 = cap_temp.read()
        cap_temp.release()
        if not ok:
            sg.popup("Cannot open source to select ROI. Make sure video path or webcam is correct.", title="ROI")
        else:
            roi_res = choose_roi_with_opencv(f0)
            if roi_res:
                worker_state["roi"] = roi_res
                append_log(f"ROI set: {roi_res}")
            else:
                append_log("ROI selection cancelled.")
    if event == "-CLEARROI-":
        worker_state["roi"] = None; append_log("ROI cleared.")
    if event == "-START-":
        if model is None or model_processor is None:
            sg.popup("Please load model first (Load Model).", title="Model required")
        else:
            if worker_thread and worker_thread.is_alive():
                sg.popup("Worker already running.", title="Running")
            else:
                # prepare worker_state from GUI
                worker_stop.clear()
                pause_flag.clear()
                worker_state["source"] = values["-SOURCE-"].strip() or "0"
                worker_state["threshold"] = values["-THR-"]/100.0
                try:
                    worker_state["infer_every"] = int(values["-INFER-"])
                except:
                    worker_state["infer_every"] = 3
                worker_state["zoom"] = values["-ZOOM-"]/100.0
                worker_state["roi"] = worker_state.get("roi", None)
                worker_state["pre_seconds"] = 3.0
                worker_state["post_seconds"] = 3.0
                worker_state["save_annotated"] = None
                worker_thread = threading.Thread(target=video_worker_thread, args=(window, worker_state), daemon=True)
                worker_thread.start()
                append_log("Worker started.")
                window["-STATUS-"].update("Running")
    if event == "-PAUSE-":
        if not pause_flag.is_set():
            pause_flag.set(); append_log("Paused.")
        else:
            pause_flag.clear(); append_log("Resumed.")
    if event == "-STOP-":
        worker_stop.set()
        if worker_thread:
            worker_thread.join(timeout=1.0)
        append_log("Stopped.")
        window["-STATUS-"].update("Stopped")
    if event == "-SNAP-":
        # save last displayed image (if any)
        imgbytes = window["-IMAGE-"].get()
        # PySimpleGUI Image cannot easily provide content back; instead read from last frame event - we store last frame bytes
        try:
            last_bytes = window.metadata.get("last_frame", None) if hasattr(window, "metadata") else None
        except:
            last_bytes = None
        if last_bytes is None:
            append_log("No frame available to snapshot.")
        else:
            fname = os.path.join(ALERTS_DIR, f"snapshot_{time.strftime('%Y%m%d_%H%M%S')}.png")
            with open(fname, "wb") as f: f.write(last_bytes)
            append_log(f"Snapshot saved: {fname}")
            refresh_alerts_list()
    if event == "-RECORD-":
        manual_recording = not manual_recording
        append_log(f"Manual record {'on' if manual_recording else 'off'}.")
    if event == "-SAVEOUT-":
        # ask user for output path
        outpath = sg.popup_get_file("Save annotated output as...", save_as=True, file_types=(("MP4","*.mp4"),), default_extension=".mp4")
        if outpath:
            worker_state["save_annotated"] = outpath
            append_log(f"Annotated output will be saved to: {outpath}")
    if event == "-REFRESHALERTS-":
        refresh_alerts_list()
    if event == "-EXPORTCSV-":
        csvpath = sg.popup_get_file("Export counts CSV", save_as=True, file_types=(("CSV","*.csv"),), default_extension=".csv")
        if csvpath:
            # We don't keep history of counts over time; export current counts only (from last -COUNTS-)
            # For more advanced logging we can add persistent storage.
            cur_counts = window["-COUNTS-"].get()
            lines = [l for l in cur_counts.splitlines() if l.strip()]
            try:
                with open(csvpath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["class","count"])
                    for l in lines:
                        if ":" in l:
                            k,v = l.split(":",1); writer.writerow([k.strip(), v.strip()])
                append_log(f"Counts exported to {csvpath}")
            except Exception as e:
                append_log(f"Export CSV failed: {e}")
    # events posted by worker
    if event == "-FRAME-":
        imgbytes = values["-FRAME-"]
        # show in Image element
        window["-IMAGE-"].update(data=imgbytes)
        # store last frame bytes for snapshot
        # monkey patch store
        if not hasattr(window, "metadata"): window.metadata = {}
        window.metadata["last_frame"] = imgbytes
    if event == "-COUNTS-":
        counts = values["-COUNTS-"]
        txt = "\n".join([f"{k}: {v}" for k,v in counts.items()]) if counts else ""
        window["-COUNTS-"].update(txt)
    if event == "-ALERT-SAVED-":
        out = values["-ALERT-SAVED-"]
        append_log(f"Evidence clip saved: {out}")
        refresh_alerts_list()
    if event == "-WORKER-LOG-":
        append_log(values["-WORKER-LOG-"])
    if event == "-FPS-":
        window["-FPS-"].update(values["-FPS-"])

# cleanup on exit
worker_stop.set()
pause_flag.clear()
append_log("Exiting.")
window.close()
