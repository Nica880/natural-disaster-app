"""v3 = v2 recipe + a 6th "Normal" (no-emergency) class.

Why: the v2 classifier saw only disaster imagery, so it MUST pick a disaster
for any input — a benign-scene audit (10 normal photos: traffic, forest,
beach, parking...) produced 6/10 false would-be incidents (parking lot →
"Flood 0.94", street → "Earthquake 0.70"...). A closed set can't say "nothing
is happening"; this teaches the classifier exactly that. The monitor gate
(EVENT_WORTHY_TYPES in app/api/routes/monitor.py) already ignores non-disaster
verdicts, so "Normal" flows through the whole stack with zero backend changes.

Data:
  Datasets/Natural Disasters/{train,valid,test}/<5 classes>/   (untouched)
  Datasets/Normal/{train,valid,test}/Normal/                   (Wikimedia bulk,
      benign scenes: traffic, streets, parking, forests, mountains, rivers,
      beaches, fields, construction, villages, winter, harbors, stations)
  fine_tune_images/<5 lowercase classes>/                      (hard cases)

Checkpoint format stays {'model','classes','accuracy'} — drop-in: the backend
reads `classes` from the file, so the 6-way head loads with no code change.

Run:  python model/train_v3.py
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
NORMAL = ROOT / "Datasets" / "Normal"
FINE_TUNE = ROOT / "fine_tune_images"
CAMERA_SIM = ROOT / "camera_sim" / "samples"
BENIGN_TEST = Path("/tmp/benign_test")        # the 10 curated end-to-end photos
OUT = Path(__file__).resolve().parent / "disaster_model_v3.pth"

EPOCHS_HEAD = 2
EPOCHS_FULL = 18
BATCH_SIZE = 32
PATIENCE = 6
DEVICE = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

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
    transforms.RandomGrayscale(p=0.05),
    transforms.RandomApply([transforms.GaussianBlur(3)], p=0.15),
    transforms.ToTensor(),
    Speckle(),
    NORM,
])
eval_tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(), NORM])

print(f"🔧 Device: {DEVICE}")

main_train = datasets.ImageFolder(DATA / "train", transform=train_tf)
classes = main_train.classes + ["Normal"]          # disaster indices unchanged
NORMAL_IDX = len(classes) - 1

def normal_split(split: str, tf):
    """Datasets/Normal/<split>/Normal/ as a dataset emitting NORMAL_IDX."""
    return datasets.ImageFolder(NORMAL / split, transform=tf,
                                target_transform=lambda _i: NORMAL_IDX)

def remapped_fine_tune():
    """fine_tune_images/ holds only (lowercase) disaster classes — remap its
    indices into the combined class list by name."""
    ft = datasets.ImageFolder(FINE_TUNE, transform=train_tf)
    by_lower = {c.lower(): i for i, c in enumerate(classes)}
    mapping = {ft_idx: by_lower[name.lower()] for name, ft_idx in ft.class_to_idx.items()}
    ft.target_transform = lambda i: mapping[i]
    return ft

train_sets = [main_train, normal_split("train", train_tf)]
if FINE_TUNE.is_dir() and any(p.is_dir() for p in FINE_TUNE.iterdir()):
    ft = remapped_fine_tune()
    train_sets.append(ft)
    print(f"📥 Merged {len(ft)} operator-collected hard cases")

val_set = ConcatDataset([datasets.ImageFolder(DATA / "valid", transform=eval_tf),
                         normal_split("valid", eval_tf)])
test_set = ConcatDataset([datasets.ImageFolder(DATA / "test", transform=eval_tf),
                          normal_split("test", eval_tf)])

train_loader = DataLoader(ConcatDataset(train_sets), batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_set, batch_size=BATCH_SIZE)
test_loader = DataLoader(test_set, batch_size=BATCH_SIZE)

n_train = sum(len(d) for d in train_sets)
print(f"📊 Train: {n_train} | Valid: {len(val_set)} | Test: {len(test_set)}")
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

for p in model.parameters():
    p.requires_grad = False
for p in model.fc.parameters():
    p.requires_grad = True
train_epochs(EPOCHS_HEAD, torch.optim.AdamW(model.fc.parameters(), lr=1e-3), tag="cap")

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

from PIL import Image  # noqa: E402

if CAMERA_SIM.is_dir():
    print("\nCamera-sim (dezastre — nu trebuie să devină Normal):")
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

if BENIGN_TEST.is_dir():
    print("\nBenign reality check (corect = Normal):")
    ok = n = 0
    for fp in sorted(BENIGN_TEST.glob("*.jpg")):
        t = eval_tf(Image.open(fp).convert("RGB")).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            probs = torch.softmax(model(t)[0], dim=0)
        idx = int(probs.argmax())
        n += 1
        ok += classes[idx] == "Normal"
        print(f"  {fp.name:26s} -> {classes[idx]:11s} ({float(probs[idx]):.2f})")
    print(f"  Normal: {ok}/{n}")
