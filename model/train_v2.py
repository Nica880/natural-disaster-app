"""Improved training recipe for the 5-class disaster classifier.

Drop-in replacement for train.py — produces the SAME checkpoint format
({'model','classes','accuracy'}) on the SAME ResNet18, so the backend
(app/services/classifier.py) needs no changes. What's different, and why:

  * Data augmentation (crops, flips, colour jitter, grayscale, blur, speckle
    noise) — the v1 model saw only clean resized images, so it latched onto
    coarse texture/colour: the 120-frame camera_sim audit showed floods called
    Earthquake/Car Crash at 0.97-1.00, and "rubble = Car Crash" on earthquake
    frames. The speckle transform mirrors the camera simulator's sensor noise.
  * 20 epochs with cosine LR + early stopping (v1: 5 fixed epochs).
  * Two-phase fine-tune: head warm-up, then full network at a low LR.
  * Label smoothing — v1 was wildly overconfident (wrong at 1.00); smoothing
    improves calibration so downstream thresholds (0.45 / 0.85) mean something.
  * fine_tune_images/ (operator-collected hard cases) merged into training.
  * Honest final report: held-out test split + the camera_sim sample frames.

Run from anywhere:  python model/train_v2.py
"""
import random
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import ConcatDataset, DataLoader
from torchvision import datasets, models, transforms
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Datasets" / "Natural Disasters"
FINE_TUNE = ROOT / "fine_tune_images"
CAMERA_SIM = ROOT / "camera_sim" / "samples"
OUT = Path(__file__).resolve().parent / "disaster_model_v2.pth"

EPOCHS_HEAD = 2          # phase 1: only the new fc layer
EPOCHS_FULL = 18         # phase 2: whole network, cosine-annealed
BATCH_SIZE = 32
PATIENCE = 6             # early-stop if val accuracy stalls this many epochs
DEVICE = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

# camera_sim folder -> class name (for the end-of-training reality check)
SIM_TRUTH = {
    "cam-accident": "Car Crash", "cam-cyclone": "Cyclone",
    "cam-earthquake": "Earthquake", "cam-fire": "Wildfire", "cam-flood": "Flood",
}


class Speckle:
    """Salt-and-pepper sensor noise, as added by the camera simulator."""

    def __init__(self, p: float = 0.30, amount: float = 0.02):
        self.p, self.amount = p, amount

    def __call__(self, t: torch.Tensor) -> torch.Tensor:
        if random.random() > self.p:
            return t
        mask = torch.rand_like(t[:1])
        t = t.clone()
        t[:, mask[0] < self.amount / 2] = 0.0
        t[:, mask[0] > 1 - self.amount / 2] = 1.0
        return t


NORM = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
train_tf = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.6, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.05),
    transforms.RandomGrayscale(p=0.05),               # archive / B&W footage
    transforms.RandomApply([transforms.GaussianBlur(3)], p=0.15),
    transforms.ToTensor(),
    Speckle(),
    NORM,
])
eval_tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(), NORM])

print(f"🔧 Device: {DEVICE}")

train_data = datasets.ImageFolder(DATA / "train", transform=train_tf)
val_data = datasets.ImageFolder(DATA / "valid", transform=eval_tf)
test_data = datasets.ImageFolder(DATA / "test", transform=eval_tf)
classes = train_data.classes

train_sets = [train_data]
if FINE_TUNE.is_dir() and any(p.is_dir() for p in FINE_TUNE.iterdir()):
    # Folder names differ only in casing ("car crash" vs "Car Crash") — both
    # sort to the same index order, so the labels align with `classes`.
    ft = datasets.ImageFolder(FINE_TUNE, transform=train_tf)
    assert [c.lower() for c in ft.classes] == [c.lower() for c in classes], \
        f"fine_tune_images classes {ft.classes} don't match {classes}"
    train_sets.append(ft)
    print(f"📥 Merged {len(ft)} operator-collected hard cases from {FINE_TUNE.name}/")

train_loader = DataLoader(ConcatDataset(train_sets), batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_data, batch_size=BATCH_SIZE)
test_loader = DataLoader(test_data, batch_size=BATCH_SIZE)

print(f"📊 Train: {sum(len(d) for d in train_sets)} | Valid: {len(val_data)} | Test: {len(test_data)}")
print(f"📂 Clase: {classes}")

model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
model.fc = nn.Linear(model.fc.in_features, len(classes))
model = model.to(DEVICE)

criterion = nn.CrossEntropyLoss(label_smoothing=0.1)


def run_eval(loader) -> float:
    model.eval()
    correct = 0
    with torch.no_grad():
        for imgs, labels in loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            correct += (model(imgs).argmax(1) == labels).sum().item()
    return correct / len(loader.dataset)


def train_epochs(n_epochs: int, optimizer, scheduler=None, tag="") -> None:
    global best_acc, stale
    for epoch in range(n_epochs):
        model.train()
        loss_sum = correct = seen = 0
        for imgs, labels in tqdm(train_loader, desc=f"{tag} {epoch + 1}/{n_epochs}"):
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            out = model(imgs)
            loss = criterion(out, labels)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * len(labels)
            correct += (out.argmax(1) == labels).sum().item()
            seen += len(labels)
        if scheduler is not None:
            scheduler.step()
        val_acc = run_eval(val_loader)
        print(f"loss {loss_sum / seen:.3f} | train acc {correct / seen:.3f} | val acc {val_acc:.3f}")
        if val_acc > best_acc:
            best_acc, stale = val_acc, 0
            torch.save({"model": model.state_dict(), "classes": classes, "accuracy": best_acc}, OUT)
            print(f"✅ Salvat {OUT.name} (val acc {best_acc:.3f})")
        else:
            stale += 1
            if stale >= PATIENCE:
                print(f"⏹ Early stop ({PATIENCE} epoci fără progres)")
                return


best_acc, stale = 0.0, 0

# Phase 1 — only the new head, backbone frozen.
for p in model.parameters():
    p.requires_grad = False
for p in model.fc.parameters():
    p.requires_grad = True
train_epochs(EPOCHS_HEAD, torch.optim.AdamW(model.fc.parameters(), lr=1e-3), tag="cap")

# Phase 2 — everything, low LR with cosine decay.
for p in model.parameters():
    p.requires_grad = True
opt = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS_FULL, eta_min=1e-6)
train_epochs(EPOCHS_FULL, opt, sched, tag="full")

# ── Final report on the BEST checkpoint ────────────────────────────────────
ckpt = torch.load(OUT, map_location=DEVICE)
model.load_state_dict(ckpt["model"])
print(f"\n🏁 Best val acc: {ckpt['accuracy']:.3f}")
print(f"🧪 Test acc: {run_eval(test_loader):.3f}")

# Per-class confusion on test
model.eval()
conf = torch.zeros(len(classes), len(classes), dtype=torch.int32)
with torch.no_grad():
    for imgs, labels in test_loader:
        preds = model(imgs.to(DEVICE)).argmax(1).cpu()
        for t, p in zip(labels, preds):
            conf[t, p] += 1
print("\nConfuzie pe test (rând=adevăr, coloană=predicție):")
print("              " + "".join(c[:9].rjust(11) for c in classes))
for i, c in enumerate(classes):
    print(c.ljust(14) + "".join(str(int(conf[i, j])).rjust(11) for j in range(len(classes))))

# Reality check on the camera simulator frames (the live demo's actual input)
if CAMERA_SIM.is_dir():
    from PIL import Image
    print("\nCamera-sim sample frames:")
    total_ok = total_n = 0
    for cam, truth in SIM_TRUTH.items():
        ok = n = 0
        for fp in sorted((CAMERA_SIM / cam).glob("frame_*.jpg")):
            t = eval_tf(Image.open(fp).convert("RGB")).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                pred = classes[int(model(t).argmax(1))]
            ok += pred == truth
            n += 1
        total_ok += ok; total_n += n
        print(f"  {cam}: {ok}/{n}")
    print(f"  TOTAL: {total_ok}/{total_n} = {100 * total_ok / total_n:.1f}%")
