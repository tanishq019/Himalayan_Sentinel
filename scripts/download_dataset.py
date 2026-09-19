"""Acquire the named public Kaggle dataset; never substitutes a fabricated source."""
from pathlib import Path
import shutil, subprocess, sys, urllib.request, zipfile
ROOT=Path(__file__).resolve().parents[1]; target=ROOT/'data'/'flood_risk_dataset_india.csv'; slug='s3programmer/flood-risk-in-india'
if target.exists(): print(f'Dataset already present: {target}'); raise SystemExit(0)
try:
 if shutil.which('kaggle'):
  subprocess.run(['kaggle','datasets','download','-d',slug,'-p',str(target.parent),'--unzip'],check=True)
 else:
  archive=target.parent/'kaggle_flood_risk.zip'; urllib.request.urlretrieve(f'https://www.kaggle.com/api/v1/datasets/download/{slug}',archive)
  with zipfile.ZipFile(archive) as z:z.extractall(target.parent)
  archive.unlink(missing_ok=True)
 if not target.exists(): raise RuntimeError('Kaggle archive did not contain flood_risk_dataset_india.csv')
 print(f'Dataset downloaded successfully: {target}')
except Exception as exc:
 print('Automatic Kaggle download was unavailable. Install/configure the Kaggle API, then run this command again, or manually download the exact file from:')
 print('https://www.kaggle.com/code/abhishridhar/floods-in-india-eda-ml-model/input')
 print(f'Place it at: {target}\nReason: {exc}')
 sys.exit(1)
