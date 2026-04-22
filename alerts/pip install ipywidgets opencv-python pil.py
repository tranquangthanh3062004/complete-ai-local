# ===================== JUPYTER NOTEBOOK ACCIDENT AI (VS CODE) =====================
# Một cell duy nhất. Chạy trong Jupyter (VS Code).
# UI: ipywidgets; Worker chạy nền; có nút Start/Pause/Stop.
# ------------------------------------------------------------------------------

import os, sys, time, math, threading, traceback, queue
from pathlib import Path
from collections import deque, OrderedDict, defaultdict
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict

import numpy as np
from PIL import Image
import cv2

# Các gói AI là tùy chọn: nếu thiếu vẫn chạy pass-through
_HAS_TORCH = _HAS_TRANS = _HAS_HF = _HAS_YOLO = False
try:
    import torch
    _HAS_TORCH = True
except Exception:
    pass
try:
    from transformers import AutoImageProcessor, DetrForObjectDetection
    _HAS_TRANS = True
except Exception:
    pass
try:
    from huggingface_hub import snapshot_download
    _HAS_HF = True
except Exception:
    pass
try:
    from ultralytics import YOLO as UltralyticsYOLO
    _HAS_YOLO = True
except Exception:
    pass

import ipywidgets as w
from IPython.display import display, clear_output

# ============================== CONFIG MẶC ĐỊNH ==============================
HF_DETR_ID_DEFAULT = "hilmantm/detr-traffic-accident-detection"
LOCAL_DETR_DIR_DEFAULT = r"C:\Users\ADMIN 88\Downloads\detr_accident_model(2)"  # thay nếu bạn có thư mục local
YOLO_MODEL_DEFAULT = "yolov8n.pt"  # nếu cài ultralytics

ALERTS_DIR = "alerts"; os.makedirs(ALERTS_DIR, exist_ok=True)
ALERTS_CSV = os.path.join(ALERTS_DIR, "alerts_log.csv")
COUNTS_CSV = os.path.join(ALERTS_DIR, "counts_log.csv")

# Hiệu năng & cảnh báo
DEFAULT_THRESHOLD      = 0.70
DEFAULT_INFER_EVERY    = 3
DEFAULT_SHORT_SIDE     = 672      # DETR shortest_edge
DEFAULT_DISPLAY_FPS    = 60
DEFAULT_DECODE_SKIP    = 1
PRE_SECONDS            = 3.0
POST_SECONDS           = 3.0
PERSIST_SEC_FOR_ALERT  = 2.0
LONG_ALERT_SECONDS     = 10.0
DUP_ALERT_SUPPRESS_SEC = 5.0
OVERLAY_SECS_AFTER_TRIGGER = 2.0
OVERLAY_ALPHA = 0.33

DEFAULT_COUNT_CLASSES = "car, truck, bus, motor, motorcycle, bicycle"

# ============================== KIỂU DỮ LIỆU CSV ==============================
@dataclass
class AlertRecord:
    timestamp: str
    evidence_video: str
    snapshot_image: str
    klass: str
    score: float
    bbox: Tuple[int,int,int,int]
    frame_index: int
    source: str

@dataclass
class CountSnapshot:
    timestamp: str
    region_counts: Dict[str,int]
    line_counts: Dict[str,int]

def _append_alert_csv(rec: AlertRecord):
    import csv
    file_exists = os.path.exists(ALERTS_CSV)
    with open(ALERTS_CSV, "a", newline="", encoding="utf-8") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(asdict(rec).keys()))
        if not file_exists: wcsv.writeheader()
        wcsv.writerow(asdict(rec))

def _append_counts_csv(snap: CountSnapshot):
    import csv
    row = {"timestamp": snap.timestamp}
    row.update({f"region:{k}": v for k,v in snap.region_counts.items()})
    row.update({f"line:{k}": v for k,v in snap.line_counts.items()})
    file_exists = os.path.exists(COUNTS_CSV)
    with open(COUNTS_CSV, "a", newline="", encoding="utf-8") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists: wcsv.writeheader()
        wcsv.writerow(row)

# ============================== HÌNH HỌC LINE ROI ==============================
def _line_side(p, a, b):
    return (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0])

def _crossed(prev_p, curr_p, a, b, min_move=4):
    if prev_p is None or curr_p is None: return False, None
    if (abs(curr_p[0]-prev_p[0])+abs(curr_p[1]-prev_p[1])) < min_move:
        return False, None
    s1 = _line_side(prev_p, a, b)
    s2 = _line_side(curr_p, a, b)
    if s1==0 or s2==0: return False, None
    if (s1>0 and s2<0) or (s1<0 and s2>0):
        direction = "A2B" if s1<0 and s2>0 else "B2A"
        return True, direction
    return False, None

# ============================== TRACKER CENTROID ===============================
class CentroidTracker:
    def __init__(self, max_disappeared=10, max_distance=80):
        self.next_id = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
    def register(self, c):
        self.objects[self.next_id] = c; self.disappeared[self.next_id]=0; self.next_id+=1
    def deregister(self, oid):
        self.objects.pop(oid, None); self.disappeared.pop(oid, None)
    def update(self, input_cents):
        if not input_cents:
            for oid in list(self.disappeared.keys()):
                self.disappeared[oid]+=1
                if self.disappeared[oid] > self.max_disappeared: self.deregister(oid)
            return self.objects
        if not self.objects:
            for c in input_cents: self.register(c)
            return self.objects
        ids = list(self.objects.keys()); existing = list(self.objects.values())
        D = np.linalg.norm(np.array(existing)[:,None]-np.array(input_cents)[None,:], axis=2)
        rows = D.min(axis=1).argsort(); cols = D.argmin(axis=1)[rows]
        usedR, usedC = set(), set()
        for r,c in zip(rows, cols):
            if r in usedR or c in usedC: continue
            if D[r,c] > self.max_distance: continue
            oid=ids[r]; self.objects[oid]=tuple(input_cents[c]); self.disappeared[oid]=0
            usedR.add(r); usedC.add(c)
        for r in range(len(existing)):
            if r not in usedR:
                oid=ids[r]; self.disappeared[oid]+=1
                if self.disappeared[oid] > self.max_disappeared: self.deregister(oid)
        for c in range(len(input_cents)):
            if c not in usedC: self.register(tuple(input_cents[c]))
        return self.objects

# ============================== DETECTOR ABSTRACTION ===========================
class BaseDetector:
    def detect(self, frame_bgr: np.ndarray, threshold: float):
        return [], [], []

class DetrDetector(BaseDetector):
    def __init__(self, path_or_id: str, use_hf: bool, short_side: int):
        if not (_HAS_TORCH and _HAS_TRANS):
            raise RuntimeError("Thiếu torch/transformers để dùng DETR.")
        if use_hf:
            self.proc = AutoImageProcessor.from_pretrained(path_or_id)
            self.net  = DetrForObjectDetection.from_pretrained(path_or_id)
        else:
            p = Path(path_or_id)
            ok = (p/"preprocessor_config.json").exists() and (p/"config.json").exists()
            ok = ok and any((p/x).exists() for x in ("model.safetensors","pytorch_model.bin","pytorch_model.safetensors"))
            if not ok and _HAS_HF:
                snapshot_download(repo_id=HF_DETR_ID_DEFAULT, local_dir=path_or_id, force_download=False)
            self.proc = AutoImageProcessor.from_pretrained(str(path_or_id))
            self.net  = DetrForObjectDetection.from_pretrained(str(path_or_id))
        self.device = "cuda" if (_HAS_TORCH and torch.cuda.is_available()) else "cpu"
        self.net.to(self.device).eval()
        if self.device == "cuda":
            try: self.net.half()
            except Exception: pass
        self.short_side = int(short_side)
    def set_short_side(self, v:int): self.short_side = int(v)
    def detect(self, frame_bgr, threshold):
        pil = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        inputs = self.proc(images=pil, return_tensors="pt",
                           do_resize=True, size={"shortest_edge": self.short_side})
        inputs = {k: v.to(self.device) for k,v in inputs.items()}
        with torch.no_grad():
            outputs = self.net(**inputs)
        target_sizes = torch.tensor([pil.size[::-1]]).to(self.device)
        results = self.proc.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=threshold)[0]
        boxes, labels, scores = [], [], []
        for s,l,b in zip(results["scores"], results["labels"], results["boxes"]):
            sc=float(s); 
            if sc < threshold: continue
            x1,y1,x2,y2 = [int(v) for v in b.tolist()]
            name = self.net.config.id2label.get(int(l.item()), str(int(l.item())))
            boxes.append((x1,y1,x2,y2)); labels.append(name); scores.append(sc)
        return boxes, labels, scores

class YoloDetector(BaseDetector):
    def __init__(self, model_name=YOLO_MODEL_DEFAULT):
        if not _HAS_YOLO: raise RuntimeError("Thiếu ultralytics để dùng YOLOv8.")
        self.model = UltralyticsYOLO(model_name)
        self.names = self.model.model.names
    def detect(self, frame_bgr, threshold):
        res = self.model.predict(source=frame_bgr, conf=threshold, verbose=False)[0]
        boxes, labels, scores = [], [], []
        for b, conf, cls_id in zip(res.boxes.xyxy.cpu().numpy(),
                                   res.boxes.conf.cpu().numpy(),
                                   res.boxes.cls.cpu().numpy().astype(int)):
            x1,y1,x2,y2 = b.astype(int)
            boxes.append((x1,y1,x2,y2))
            labels.append(self.names.get(cls_id, str(cls_id)))
            scores.append(float(conf))
        return boxes, labels, scores

# ============================== VẼ OVERLAY CẢNH BÁO ============================
def _draw_alert_overlay(frame, text="ACCIDENT ALERT", alpha=OVERLAY_ALPHA):
    h,w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0,0), (w,h), (0,0,255), -1)
    cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)
    scale = max(1.0, w/900)
    cv2.putText(frame, text, (int(0.07*w), int(0.12*h)),
                cv2.FONT_HERSHEY_SIMPLEX, 2.2*scale, (255,255,255), 4, cv2.LINE_AA)

# ============================== UI WIDGETS ======================================
# khối hiển thị video
img = w.Image(format='png', width=960, height=540)

# Model
backend_dd   = w.Dropdown(options=["(No AI) Pass-through", "DETR (HuggingFace)", "YOLOv8 (Ultralytics)"],
                          value="(No AI) Pass-through", description="Backend")
use_hf_chk   = w.Checkbox(value=True, description="Use HF DETR id")
hf_id_txt    = w.Text(value=HF_DETR_ID_DEFAULT, description="HF id")
local_dir_txt= w.Text(value=LOCAL_DETR_DIR_DEFAULT, description="Local DETR")
yolo_path_txt= w.Text(value=YOLO_MODEL_DEFAULT, description="YOLO model")
btn_load     = w.Button(description="Load Model", button_style='success')
model_status = w.Label(value="Model: idle")

# Source & Smoothness
src_txt      = w.Text(value="0", description="Source")
thr_sld      = w.FloatSlider(value=DEFAULT_THRESHOLD, min=0.05, max=1.0, step=0.01, description="Threshold")
infer_spn    = w.IntSlider(value=DEFAULT_INFER_EVERY, min=1, max=60, step=1, description="Infer every N")
short_spn    = w.IntSlider(value=DEFAULT_SHORT_SIDE, min=256, max=1280, step=16, description="DETR short side")
fps_cap_spn  = w.IntSlider(value=DEFAULT_DISPLAY_FPS, min=1, max=120, step=1, description="Display FPS cap")
skip_spn     = w.IntSlider(value=DEFAULT_DECODE_SKIP, min=0, max=10, step=1, description="Decode skip")

# ROI
btn_set_regions = w.Button(description="Set REGION rectangles (multi)")
btn_set_lines   = w.Button(description="Set LINEs (max 3)")
region_txt      = w.Textarea(placeholder="rx,ry,rw,rh per line (normalized)", layout=w.Layout(height="70px"))
lines_txt       = w.Textarea(placeholder="x1,y1,x2,y2 per line (normalized)", layout=w.Layout(height="70px"))
classes_txt     = w.Text(value=DEFAULT_COUNT_CLASSES, description="Count classes")

# Controls
btn_start   = w.Button(description="Start", button_style='primary')
btn_pause   = w.Button(description="Pause/Resume")
btn_stop    = w.Button(description="Stop", button_style='danger')
btn_snap    = w.Button(description="Snapshot")
btn_export  = w.Button(description="Export counts CSV")

# Panels
region_area = w.Textarea(layout=w.Layout(height="80px"))
line_area   = w.Textarea(layout=w.Layout(height="80px"))
logs_area   = w.Textarea(value="Ready.\n", layout=w.Layout(height="160px"))

# layout
controls_left = w.VBox([
    backend_dd, use_hf_chk, hf_id_txt, local_dir_txt, yolo_path_txt, btn_load, model_status,
    w.HBox([src_txt]),
    thr_sld, w.HBox([infer_spn, short_spn]), w.HBox([fps_cap_spn, skip_spn]),
    btn_set_regions, region_txt, btn_set_lines, lines_txt, classes_txt,
    w.HBox([btn_start, btn_pause, btn_stop, btn_snap, btn_export])
])
controls_right = w.VBox([
    w.Label("Region counts"), region_area,
    w.Label("Line crossings"), line_area,
    w.Label("Logs"), logs_area
])
ui = w.HBox([w.VBox([img]), w.VBox([controls_left, controls_right])], layout=w.Layout(align_items='flex-start'))
display(ui)

# ============================== TRẠNG THÁI TOÀN CỤC =============================
GLOBAL = {
    "detector": None,
    "worker": None,
    "ui_thread": None,
    "stop_event": threading.Event(),
    "pause_event": threading.Event(),
    "q": queue.Queue(),
}

def _log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    logs_area.value += f"{ts} - {msg}\n"
    if len(logs_area.value) > 10000:
        logs_area.value = logs_area.value[-8000:]

def _safe_stop():
    """Dừng worker cũ nếu cell chạy lại."""
    try:
        if GLOBAL["worker"] and GLOBAL["worker"].is_alive():
            GLOBAL["stop_event"].set()
            GLOBAL["worker"].join(timeout=2.0)
    except Exception:
        pass
    try:
        if GLOBAL["ui_thread"] and GLOBAL["ui_thread"].is_alive():
            GLOBAL["ui_thread"].join(timeout=1.0)
    except Exception:
        pass
    GLOBAL["stop_event"].clear()
    GLOBAL["pause_event"].clear()
    GLOBAL["worker"] = None
    GLOBAL["ui_thread"] = None

# ============================== LOADER MÔ HÌNH ==============================
def on_load_model(b):
    _safe_stop()  # không cần, nhưng đảm bảo clear trước khi nạp mới
    backend = backend_dd.value
    try:
        if backend.startswith("(No AI)"):
            GLOBAL["detector"] = None
            model_status.value = "Model: pass-through"
            _log("Using pass-through (no AI).")
        elif backend.startswith("DETR"):
            use_hf = bool(use_hf_chk.value)
            path = hf_id_txt.value.strip() if use_hf else local_dir_txt.value.strip()
            det = DetrDetector(path_or_id=path, use_hf=use_hf, short_side=int(short_spn.value))
            GLOBAL["detector"] = det
            model_status.value = f"Model: DETR ({'HF' if use_hf else 'local'})"
            _log("DETR loaded.")
        else:
            det = YoloDetector(yolo_path_txt.value.strip())
            GLOBAL["detector"] = det
            model_status.value = "Model: YOLOv8"
            _log("YOLOv8 loaded.")
    except Exception as e:
        GLOBAL["detector"] = None
        model_status.value = "Model: load failed"
        _log(f"Load model failed: {e}\n{traceback.format_exc()}")

btn_load.on_click(on_load_model)

# ============================== WORKER VIDEO ==============================
def _bgr_to_png_bytes(frame):
    _, buf = cv2.imencode(".png", frame)
    return buf.tobytes()

def _save_clip(frames, filename, fps):
    if not frames: return False
    h,w = frames[0].shape[:2]
    writer = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*"mp4v"), max(1.0, fps), (w,h))
    for f in frames: writer.write(f)
    writer.release(); return True

def _ui_updater():
    """Đọc queue và cập nhật widgets (chạy background thread)."""
    while not GLOBAL["stop_event"].is_set():
        try:
            typ, data = GLOBAL["q"].get(timeout=0.15)
        except queue.Empty:
            continue
        if typ == "frame":
            img.value = data
        elif typ == "log":
            _log(data)
        elif typ == "region":
            region_area.value = "\n".join([f"{k}: {v}" for k,v in data.items()])
        elif typ == "line":
            line_area.value = "\n".join([f"{k}: {v}" for k,v in data.items()])

def _select_regions_from_source(src):
    try:
        srcv = int(src) if str(src).isdigit() else src
    except:
        srcv = src
    cap = cv2.VideoCapture(srcv); ok, f0 = cap.read(); cap.release()
    if not ok: 
        _log("Cannot open source for REGION selection."); return []
    rois = cv2.selectROIs("Select REGIONS - ENTER to confirm", f0, False, False)
    cv2.destroyAllWindows()
    h,w = f0.shape[:2]
    regs=[]
    for (x,y,wid,hei) in rois:
        if wid>0 and hei>0:
            regs.append((x/w, y/h, wid/w, hei/h))
    return regs

def _select_lines_from_source(src, max_lines=3):
    try:
        srcv = int(src) if str(src).isdigit() else src
    except:
        srcv = src
    cap = cv2.VideoCapture(srcv); ok, f0 = cap.read(); cap.release()
    if not ok: 
        _log("Cannot open source for LINE selection."); return []
    clone=f0.copy(); pts=[]
    def on_mouse(event,x,y,flags,param):
        nonlocal clone, pts
        if event==cv2.EVENT_LBUTTONDOWN:
            pts.append((x,y))
            if len(pts)%2==0:
                cv2.line(clone, pts[-2], pts[-1], (0,140,255), 4)
            cv2.imshow("Draw LINEs: click 2 points/line, ESC to finish", clone)
    cv2.imshow("Draw LINEs: click 2 points/line, ESC to finish", clone)
    cv2.setMouseCallback("Draw LINEs: click 2 points/line, ESC to finish", on_mouse)
    while True:
        key=cv2.waitKey(10) & 0xFF
        if key==27: break
        if len(pts)//2 >= max_lines: break
    cv2.destroyAllWindows()
    h,w = f0.shape[:2]
    lines=[]
    for i in range(0, len(pts)-1, 2):
        a=pts[i]; b=pts[i+1]
        lines.append(((a[0]/w, a[1]/h), (b[0]/w, b[1]/h)))
    return lines

def _start_worker():
    """Khởi chạy worker theo config hiện tại."""
    _safe_stop()
    GLOBAL["stop_event"].clear()
    GLOBAL["pause_event"].clear()

    # UI updater thread
    ui_t = threading.Thread(target=_ui_updater, daemon=True)
    ui_t.start()
    GLOBAL["ui_thread"] = ui_t

    # Snapshot các tham số
    source = src_txt.value.strip() or "0"
    threshold = float(thr_sld.value)
    inferN = int(infer_spn.value)
    short_side = int(short_spn.value)
    fps_cap = int(fps_cap_spn.value)
    decode_skip = int(skip_spn.value)
    cnt_classes = [c.strip().lower() for c in classes_txt.value.split(",") if c.strip()]

    # parse ROI từ Textarea
    regions=[]
    for line in region_txt.value.strip().splitlines():
        if not line.strip(): continue
        rx,ry,rw,rh = [float(x) for x in line.split(",")]
        regions.append((rx,ry,rw,rh))
    lines=[]
    for line in lines_txt.value.strip().splitlines():
        if not line.strip(): continue
        x1,y1,x2,y2 = [float(x) for x in line.split(",")]
        lines.append(((x1,y1),(x2,y2)))

    det = GLOBAL["detector"]  # có thể None

    def work():
        """Luồng xử lý video + AI."""
        # mở nguồn hoặc fallback
        try:
            srcv = int(source) if source.isdigit() else source
        except:
            srcv = source
        cap = cv2.VideoCapture(srcv)
        mode = "source"
        if not cap.isOpened():
            # fallback webcam 0
            cap = cv2.VideoCapture(0)
            mode = "webcam"
        if not cap.isOpened():
            GLOBAL["q"].put(("log", "Fallback synthetic frames."))
            cap = None
            mode = "synthetic"
        else:
            GLOBAL["q"].put(("log", f"Started ({mode})"))

        fps_native = cap.get(cv2.CAP_PROP_FPS) or 25.0 if cap else 25.0
        prebuf = deque(maxlen=max(1, int(PRE_SECONDS*fps_native)))

        tracker = CentroidTracker()
        prev_pos = {}
        region_counts = defaultdict(int)
        line_counts   = defaultdict(int)
        seen_region_ids = set()

        alert_since = None
        last_alert = 0.0
        overlay_until = 0.0

        frame_idx = 0
        prev_emit = 0.0

        # main loop
        while not GLOBAL["stop_event"].is_set():
            if GLOBAL["pause_event"].is_set():
                time.sleep(0.03); continue

            ok=False
            if cap is not None:
                # decode skip
                for _ in range(decode_skip+1):
                    r, frame = cap.read()
                    if not r: ok=False; break
                    ok=True
                if not ok:
                    GLOBAL["q"].put(("log","End of stream.")); break
            else:
                # synthetic
                w,h = 960,540
                frame = np.zeros((h,w,3), np.uint8)
                t=time.time()
                cv2.putText(frame, f"SYNTHETIC {t:.1f}", (40,120), cv2.FONT_HERSHEY_SIMPLEX, 2, (60,60,255), 3)
                cv2.circle(frame, (int((math.sin(t)*0.4+0.5)*w), h//2), 50, (0,180,255), -1)
                ok=True

            frame_idx += 1
            prebuf.append(frame.copy())

            # inference
            boxes=[]; labels=[]; scores=[]
            if det and (frame_idx % max(1,inferN) == 0):
                try:
                    if isinstance(det, DetrDetector):
                        det.set_short_side(short_side)
                    boxes, labels, scores = det.detect(frame, threshold=threshold)
                except Exception as e:
                    GLOBAL["q"].put(("log", f"Inference error: {e}"))

            # tracking
            cents = [(x1+(x2-x1)//2, y1+(y2-y1)//2) for (x1,y1,x2,y2) in boxes]
            objects = tracker.update(cents)

            # id->label gần nhất
            id2label={}
            for oid, c in objects.items():
                if not cents: id2label[oid]=None; continue
                d=[math.hypot(c[0]-cc[0], c[1]-cc[1]) for cc in cents]
                j=int(np.argmin(d))
                id2label[oid] = labels[j] if d[j] < 100 else None

            h,w = frame.shape[:2]

            # vẽ REGION
            for ri,(rx,ry,rw,rh) in enumerate(regions):
                x1,y1,x2,y2 = int(rx*w), int(ry*h), int((rx+rw)*w), int((ry+rh)*h)
                cv2.rectangle(frame, (x1,y1),(x2,y2), (20,180,255), 3)
                cv2.putText(frame, f"REG{ri}", (x1, max(18,y1-8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20,180,255), 2)

            # đếm region
            valid_classes = [c.strip().lower() for c in cnt_classes]
            for oid, c in objects.items():
                lab = id2label.get(oid)
                if not lab: continue
                if not any(k in lab.lower() for k in valid_classes): continue
                for ri,(rx,ry,rw,rh) in enumerate(regions):
                    x1,y1,x2,y2 = int(rx*w), int(ry*h), int((rx+rw)*w), int((ry+rh)*h)
                    if x1<=c[0]<=x2 and y1<=c[1]<=y2 and (oid,ri) not in seen_region_ids:
                        region_counts[lab]+=1; seen_region_ids.add((oid,ri))

            # vẽ LINE + đếm qua vạch
            for li,(pa_n, pb_n) in enumerate(lines):
                pa=(int(pa_n[0]*w), int(pa_n[1]*h))
                pb=(int(pb_n[0]*w), int(pb_n[1]*h))
                cv2.line(frame, pa, pb, (0,140,255), 4)
                cv2.putText(frame, f"L{li}", ((pa[0]+pb[0])//2, (pa[1]+pb[1])//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,140,255), 2)

            for oid, c in objects.items():
                prev = prev_pos.get(oid)
                for li,(pa_n,pb_n) in enumerate(lines):
                    pa=(int(pa_n[0]*w), int(pa_n[1]*h))
                    pb=(int(pb_n[0]*w), int(pb_n[1]*h))
                    okc, direction = _crossed(prev, c, pa, pb)
                    if okc:
                        key=f"L{li}_{direction}"
                        line_counts[key]+=1
                prev_pos[oid]=c

            # vẽ bbox + ID
            accident_present=False
            top_acc=(None,-1.0,None)
            for i,(x1,y1,x2,y2) in enumerate(boxes):
                cls, sc = labels[i], scores[i]
                col=(0,190,60)
                if any(k in cls.lower() for k in ("accident","crash","collision")):
                    col=(0,0,255); accident_present=True
                    if sc>top_acc[1]: top_acc=((x1,y1,x2,y2), sc, cls)
                cv2.rectangle(frame,(x1,y1),(x2,y2),col,2)
                cv2.putText(frame, f"{cls} {sc:.2f}", (x1, max(16,y1-8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)

            for oid,c in objects.items():
                cv2.putText(frame, f"ID{oid}", (c[0]-10, c[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (30,120,255), 2)

            # cảnh báo tai nạn (bền vững)
            now=time.time()
            if accident_present:
                if alert_since is None: alert_since=now
                dur = now - (alert_since or now)
                if dur>=LONG_ALERT_SECONDS and (now-last_alert>DUP_ALERT_SUPPRESS_SEC):
                    _trigger_alert(cap, prebuf, fps_native, frame, top_acc, critical=True, source=source, frame_idx=frame_idx)
                    last_alert=now; alert_since=now
                elif dur>=PERSIST_SEC_FOR_ALERT and (now-last_alert>DUP_ALERT_SUPPRESS_SEC):
                    _trigger_alert(cap, prebuf, fps_native, frame, top_acc, critical=False, source=source, frame_idx=frame_idx)
                    last_alert=now; alert_since=now
                overlay_until = max(overlay_until, now + OVERLAY_SECS_AFTER_TRIGGER)
            else:
                alert_since=None

            if now < overlay_until:
                _draw_alert_overlay(frame)

            # emit với FPS cap (giữ tốc độ bình thường, mượt)
            min_interval = 1.0/float(max(1,fps_cap))
            tnow=time.time()
            if tnow - prev_emit >= min_interval:
                prev_emit = tnow
                GLOBAL["q"].put(("frame", _bgr_to_png_bytes(frame)))
                GLOBAL["q"].put(("region", dict(sorted(region_counts.items()))))
                GLOBAL["q"].put(("line", dict(sorted(line_counts.items()))))
            else:
                time.sleep(max(0.0, min_interval-(tnow-prev_emit)))

        if cap is not None: cap.release()
        GLOBAL["q"].put(("log","Worker ended."))

    def _trigger_alert(cap, prebuf, fps, frame_now, top_accident, critical, source, frame_idx):
        ts=time.strftime("%Y%m%d_%H%M%S")
        frames_to_save=list(prebuf)
        # lấy thêm post-seconds
        if cap is not None:
            for _ in range(int(POST_SECONDS*fps)):
                r2,f2=cap.read()
                if not r2: break
                frames_to_save.append(f2)
        ev=os.path.join(ALERTS_DIR, f"evidence_{'CRIT_' if critical else ''}{ts}.mp4")
        _save_clip(frames_to_save, ev, fps)
        snap=os.path.join(ALERTS_DIR, f"snapshot_{'CRIT_' if critical else ''}{ts}.png")
        cv2.imwrite(snap, frame_now)
        # beep
        try:
            import winsound; winsound.Beep(1200 if critical else 1000, 700 if critical else 500)
        except Exception:
            pass
        # csv log
        bbox, sc, cls = top_accident
        _append_alert_csv(AlertRecord(ts, ev, snap, str(cls) if cls else "", float(sc) if sc else -1.0,
                                      tuple(bbox) if bbox else (-1,-1,-1,-1), int(frame_idx), str(source)))
        GLOBAL["q"].put(("log", f"{'CRITICAL ' if critical else ''}Accident alert saved: {ev} | {snap}"))

    t = threading.Thread(target=work, daemon=True)
    t.start()
    GLOBAL["worker"] = t
    _log("Worker started.")

# ============================== NÚT ROI HANDLERS ==============================
def on_set_regions(b):
    regs = _select_regions_from_source(src_txt.value.strip() or "0")
    if regs:
        region_txt.value = "\n".join([f"{r[0]:.4f},{r[1]:.4f},{r[2]:.4f},{r[3]:.4f}" for r in regs])
        _log(f"Set {len(regs)} REGION(s).")

def on_set_lines(b):
    lines = _select_lines_from_source(src_txt.value.strip() or "0", max_lines=3)
    if lines:
        lines_txt.value = "\n".join([f"{a[0]:.4f},{a[1]:.4f},{b[0]:.4f},{b[1]:.4f}" for a,b in lines])
        _log(f"Set {len(lines)} LINE(s).")

btn_set_regions.on_click(on_set_regions)
btn_set_lines.on_click(on_set_lines)

# ============================== NÚT ĐIỀU KHIỂN ==============================
def on_start(b):
    _start_worker()

def on_pause(b):
    if GLOBAL["pause_event"].is_set():
        GLOBAL["pause_event"].clear(); _log("Resumed.")
    else:
        GLOBAL["pause_event"].set(); _log("Paused.")

def on_stop(b):
    _safe_stop(); _log("Stop requested.")

def on_snapshot(b):
    # Lấy khung hiện tại từ img.value
    if img.value:
        fn=os.path.join(ALERTS_DIR, f"snapshot_{time.strftime('%Y%m%d_%H%M%S')}.png")
        with open(fn, "wb") as f:
            f.write(img.value)
        _log(f"Snapshot saved: {fn}")
    else:
        _log("No frame to snapshot.")

def on_export_counts(b):
    # xuất nhanh nội dung panel ra CSV
    r = {}
    for line in region_area.value.splitlines():
        if ":" in line:
            k,v=line.split(":",1); r[k.strip()]=int(v.strip())
    l = {}
    for line in line_area.value.splitlines():
        if ":" in line:
            k,v=line.split(":",1); l[k.strip()]=int(v.strip())
    _append_counts_csv(CountSnapshot(time.strftime("%Y%m%d_%H%M%S"), r, l))
    _log("Counts snapshot exported.")

btn_start.on_click(on_start)
btn_pause.on_click(on_pause)
btn_stop.on_click(on_stop)
btn_snap.on_click(on_snapshot)
btn_export.on_click(on_export_counts)

# ============================== KẾT THÚC SETUP ==============================
_log("UI ready. Chọn backend (nếu cần) -> Load Model -> đặt Source -> Set ROI/LINE (tuỳ) -> Start.")

