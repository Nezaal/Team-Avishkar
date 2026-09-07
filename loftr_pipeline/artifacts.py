"""Save inspectable artifacts, including failure diagnostics, without invented results."""
import csv
import html
import json
from pathlib import Path

import cv2
import numpy as np


def write_image(path, image):
    if not cv2.imwrite(str(path), image):
        raise OSError(f"Could not write {path}")


def write_artifacts(output, result, source, reference, matches0, matches1, scores, inliers,
                    registered=None, overlap=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    files = {}
    def save(name, image):
        write_image(output / name, image)
        files[name.split('.')[0]] = name
    save("source.png", source)
    save("reference.png", reference)
    # Cap visualization only; CSV retains every filtered match and inlier flag.
    order = np.argsort(-scores)[:250]
    kp0 = [cv2.KeyPoint(float(p[0]), float(p[1]), 3) for p in matches0]
    kp1 = [cv2.KeyPoint(float(p[0]), float(p[1]), 3) for p in matches1]
    dm = [cv2.DMatch(int(i), int(i), 0.) for i in order]
    canvas = cv2.drawMatches(source, kp0, reference, kp1, dm, None,
                             matchColor=(40, 200, 80), singlePointColor=(150, 150, 150),
                             matchesMask=[int(inliers[i]) for i in order], flags=2)
    save("matches.png", canvas)
    if not inliers.any() and len(order):
        save("tentative_matches.png", cv2.drawMatches(source, kp0, reference, kp1, dm, None, flags=2))
    if registered is not None:
        save("registered.png", registered)
        save("valid_overlap.png", overlap)
        blend = reference.copy()
        blended = cv2.addWeighted(reference, .5, registered, .5, 0)
        blend[overlap > 0] = blended[overlap > 0]
        save("overlay.png", blend)
        yy, xx = np.indices(reference.shape)
        checker = reference.copy()
        use = ((xx // 48 + yy // 48) % 2 == 0) & (overlap > 0)
        checker[use] = registered[use]
        save("checkerboard.png", checker)
    rows = result["correspondences"]
    fields = ["ohrc_x", "ohrc_y", "tmc2_x", "tmc2_y", "match_confidence", "inlier", "error_tmc2_px"]
    with (output / "correspondences.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    files["correspondences"] = "correspondences.csv"
    if result.get("transformation"):
        (output / "transform.json").write_text(json.dumps(result["transformation"], indent=2), encoding="utf-8")
        files["transform"] = "transform.json"
    files.update({"report": "report.html", "result": "result.json"})
    result["artifacts"] = files
    (output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    # A portable static evidence report; the API also serves its referenced artifacts.
    cards = "".join(f'<figure><figcaption>{html.escape(k.replace("_", " "))}</figcaption><img src="{v}" alt="{html.escape(k)}"></figure>'
                    for k, v in files.items() if v.endswith(".png"))
    summary = {k: v for k, v in result.items() if k not in ("correspondences", "artifacts")}
    body = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>LoFTR registration evidence</title><style>body{{font:16px system-ui;background:#f4f6fa;color:#15243b;margin:28px}}
h1{{font-size:24px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}}figure{{margin:0;background:white;padding:16px;border-radius:10px}}
img{{width:100%;height:auto}}pre{{overflow:auto;background:white;padding:20px;font-size:14px}}figcaption{{margin-bottom:10px;font-weight:600}}</style>
<h1>{html.escape(result['pair_id'])} · {html.escape(result['status'])}</h1>
<p>Pretrained LoFTR baseline. Reprojection residuals are fitting errors, not independent ground-truth accuracy.</p>
<p><a href="result.json">Result JSON</a> · <a href="correspondences.csv">Correspondences CSV</a></p>
<div class="grid">{cards}</div><pre>{html.escape(json.dumps(summary, indent=2))}</pre></html>'''
    (output / "report.html").write_text(body, encoding="utf-8")
    return result
