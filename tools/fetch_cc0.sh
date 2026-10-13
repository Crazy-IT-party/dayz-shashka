#!/usr/bin/env bash
# The photos the textures are built from (tools/build_model.py), all CC0 (no attribution needed):
#  - ambientCG material sets, 1K JPG, unpacked into build/cc0/<asset>/
#  - the reference shashka (Livrustkammaren 1315, Wikimedia Commons), original scan -> build/ref/shashka_ref_hi.png
#   Metal009 brushed steel - blade brushing, scratches on the silver | Leather037 leather - scabbard grain
#   Metal056B rusted iron - damage
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/cc0
for a in Metal009 Leather037 Metal056B; do
  [ -d build/cc0/$a ] && continue
  curl -sfL -m 300 -o build/cc0/$a.zip "https://ambientcg.com/get?file=${a}_1K-JPG.zip"
  python3 -I - build/cc0/$a.zip build/cc0/$a <<'PY'
import sys, zipfile, pathlib
z, d = sys.argv[1], pathlib.Path(sys.argv[2])
d.mkdir(exist_ok=True)
with zipfile.ZipFile(z) as f:
    for n in f.namelist():
        if n.lower().endswith((".jpg", ".png")) and "/" not in n and ".." not in n:
            (d / n).write_bytes(f.read(n))
PY
  rm -f build/cc0/$a.zip
  echo "fetched $a"
done
if [ ! -f build/ref/shashka_ref_hi.png ]; then
  mkdir -p build/ref
  curl -sfL -m 900 -A "dayz-shashka-build" -o build/ref/ref_orig.tif \
    "https://upload.wikimedia.org/wikipedia/commons/c/c3/Sabel%2C_schaschka_-_Livrustkammaren_-_1315_%28cropped%29.tif"
  python3 -I - build/ref/ref_orig.tif build/ref/shashka_ref_hi.png <<'PY'
import sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
a = np.asarray(Image.open(sys.argv[1]).convert("L"), np.float32)
lo, hi = np.percentile(a, 0.5), np.percentile(a, 99.8)
Image.fromarray((((a - lo) / (hi - lo)).clip(0, 1) * 255).astype(np.uint8)).save(sys.argv[2])
PY
  rm -f build/ref/ref_orig.tif
  echo "fetched the reference shashka"
fi
