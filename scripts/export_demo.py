#!/usr/bin/env python3
"""
Export ESR demo data: one JSON per curated CLEVRER test video + index.json.
Joins CLEVRER trajectories, named facts per rung, and KARMA per-query scores per rung.
Queries are joined across rungs by NAME key (video, subject, target, cutoff bin).
Run from physt_kg/:  python export_demo.py --out demo_data --n-videos 24
"""
import argparse, glob, json, os, re
from collections import defaultdict, Counter
import numpy as np

RUNGS = [  # (key, label, data dir, preds npz)
    ("events", "Events only",        "data/physt_clevrer_nokin",    "preds_karma_nokin_fc_demo.npz"),
    ("kin",    "+ Kinematics",       "data/physt_clevrer",          "preds_karma_kin_fc_demo.npz"),
    ("rel",    "+ Relative motion",  "data/physt_clevrer_rel",      "preds_karma_rel_fc_demo.npz"),
    ("rel128", "+ Long look-ahead",  "data/physt_clevrer_rel_h128", "preds_karma_relh128_fc_s42_demo.npz"),
]
ENT = re.compile(r"^v(\d+)_o(\d+)$")


def read_ids(path):
    m = {}
    for line in open(path):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 2:
            m[int(p[1])] = p[0]
    return m


def read_named(path):
    out = []
    if os.path.exists(path):
        for line in open(path):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 4:
                out.append((p[0], p[1], p[2], int(p[3])))
    return out


def vid_of(name):
    m = ENT.match(name)
    return (m.group(1), int(m.group(2))) if m else (None, None)


def load_rung(key, ddir, npz):
    id2ent = read_ids(os.path.join(ddir, "entity2id.txt"))
    d = np.load(os.path.join(ddir, npz))
    sc, C, M, S, TGT = d["scores"], d["C"], d["M"], d["S"], d["TGT"]
    tau, HZ, t_range = d["tau"], d["HZ"], float(d["t_range"])
    n = len(S); ar = np.arange(n)
    valid = M > 0
    if not valid[ar, TGT].all():        # the target slot must be valid
        valid = ~valid
    assert valid[ar, TGT].all(), f"{key}: mask orientation unclear (target slot invalid)"
    out = {}
    for i in range(n):
        s = id2ent[int(S[i])]; vid, s_oid = vid_of(s)
        cut = int(round(float(tau[i]) * t_range))
        cands = [int(c) for c, ok in zip(C[i], valid[i]) if ok]
        cscores = [float(x) for x, ok in zip(sc[i], valid[i]) if ok]
        coids = [vid_of(id2ent[c])[1] for c in cands]
        tgt = vid_of(id2ent[int(C[i, TGT[i]])])[1]
        ts = cscores[coids.index(tgt)]
        rank = 1 + sum(x > ts for x in cscores) + 0.5 * (sum(x == ts for x in cscores) - 1)
        out[(vid, s_oid, tgt, cut)] = dict(cands=coids, scores=cscores, rank=rank, hz=int(HZ[i]))
    return out


def find_ann(ann_root, vid):
    hits = glob.glob(os.path.join(ann_root, "**", f"annotation_{int(vid):05d}.json"), recursive=True)
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ann-root", default="clevrer_ann")
    ap.add_argument("--out", default="demo_data")
    ap.add_argument("--n-videos", type=int, default=24)
    ap.add_argument("--frame-step", type=int, default=1, help="keep every k-th frame")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    meta = json.load(open(os.path.join(RUNGS[-1][2], "meta.json")))
    bin_size = int(meta["bin_size"])

    preds = {}
    for key, _, ddir, npz in RUNGS:
        if os.path.exists(os.path.join(ddir, npz)):
            preds[key] = load_rung(key, ddir, npz); print(f"{key}: {len(preds[key])} queries")
        else:
            print(f"{key}: MISSING {npz} (skipped)")
    have = [k for k, *_ in RUNGS if k in preds]
    assert have, "no prediction files found"
    common = set.intersection(*[set(preds[k]) for k in have])
    print(f"queries present in all {len(have)} rungs: {len(common)}")

    facts = {k: defaultdict(list) for k in have}
    for key, _, ddir, _ in RUNGS:
        if key not in have:
            continue
        for split_file, phase in (("test_context.txt", "history"), ("test.txt", "future")):
            for h, r, t, b in read_named(os.path.join(ddir, "named", split_file)):
                vid, _ = vid_of(h)
                if vid is not None:
                    facts[key][vid].append([h.split("_o")[-1], r,
                                            t.split("_o")[-1] if ENT.match(t) else t, b, phase])

    # ---- curation scores per video
    byvid = defaultdict(list)
    for q in common:
        byvid[q[0]].append(q)
    top, bot = have[-1], have[0]
    avail = {str(int(re.search(r"annotation_(\d+)\.json", p).group(1)))
             for p in glob.glob(os.path.join(a.ann_root, "**", "annotation_*.json"), recursive=True)}
    miss = [v for v in byvid if str(int(v)) not in avail]
    print(f"annotations found for {len(byvid) - len(miss)}/{len(byvid)} test videos")
    cands = []
    for vid, qs in byvid.items():
        if str(int(vid)) not in avail:
            continue
        gain = sum(preds[bot][q]["rank"] - preds[top][q]["rank"] for q in qs)
        far = sum(preds[top][q]["hz"] >= 6 for q in qs)
        fail = sum(preds[top][q]["rank"] > 1 for q in qs)
        cands.append((vid, gain, far, fail, len(qs)))

    picks, tags = [], {}
    def take(lst, tag, k):
        for v in lst:
            if len([p for p in picks if tags[p] == tag]) >= k:
                break
            if v[0] not in tags:
                picks.append(v[0]); tags[v[0]] = tag
    k = max(1, a.n_videos // 4)
    take(sorted(cands, key=lambda c: -c[1]), "vocabulary_helps", k)
    take(sorted(cands, key=lambda c: (-c[2], -c[1])), "long_horizon", k)
    take(sorted(cands, key=lambda c: -c[3]), "failure", k)

    # occlusion: subject or target out of camera view before the cutoff
    occl, index, ann_cache = [], [], {}
    for vid, *_ in sorted(cands, key=lambda c: -c[4]):
        if vid in tags:
            continue
        p = find_ann(a.ann_root, vid)
        if not p:
            continue
        ann = json.load(open(p)); ann_cache[vid] = ann
        cut_f = int(meta["videos"].get(vid, {}).get("cutoff_frame", 8 * bin_size - 1)) + 1
        hidden = set()
        for fr in ann["motion_trajectory"][:cut_f]:
            for o in fr["objects"]:
                if not o.get("inside_camera_view", True):
                    hidden.add(o["object_id"])
        if any(q[1] in hidden or q[2] in hidden for q in byvid[vid]):
            occl.append((vid,))
        if len(occl) >= k:
            break
    take(occl, "occlusion", k)

    for vid in picks:
        ann = ann_cache.get(vid) or json.load(open(find_ann(a.ann_root, vid)))
        props = {o["object_id"]: o for o in ann["object_property"]}
        frames = []
        for fr in ann["motion_trajectory"][::a.frame_step]:
            row = {}
            for o in fr["objects"]:
                x, y = o["location"][:2]; vx, vy = o["velocity"][:2]
                row[o["object_id"]] = [round(x, 3), round(y, 3), round(vx, 3), round(vy, 3),
                                       int(bool(o.get("inside_camera_view", True)))]
            frames.append(row)
        qs = sorted(byvid[vid], key=lambda q: (q[3], q[1], q[2]))
        out = {
            "video": vid, "tag": tags[vid], "bin_size": bin_size, "frame_step": a.frame_step,
            "n_frames": len(ann["motion_trajectory"]),
            "cutoff_bin": meta["videos"].get(vid, {}).get("cutoff_bin"),
            "rungs": [{"key": k_, "label": l} for k_, l, *_ in RUNGS if k_ in have],
            "objects": [{"oid": i, "shape": p.get("shape"), "color": p.get("color"),
                         "material": p.get("material")} for i, p in sorted(props.items())],
            "frames": frames,
            "collisions": [{"frame": c["frame_id"], "objects": c["object_ids"]} for c in ann.get("collision", [])],
            "facts": {k_: facts[k_].get(vid, []) for k_ in have},
            "queries": [{"subject": q[1], "target": q[2], "cutoff_bin": q[3],
                         "horizon": preds[top][q]["hz"],
                         "preds": {k_: {"cands": preds[k_][q]["cands"],
                                        "scores": [round(s, 4) for s in preds[k_][q]["scores"]],
                                        "rank": preds[k_][q]["rank"]} for k_ in have}}
                        for q in qs],
        }
        json.dump(out, open(os.path.join(a.out, f"video_{vid}.json"), "w"), separators=(",", ":"))
        index.append({"video": vid, "tag": tags[vid], "n_queries": len(qs),
                      "rank_top": [preds[top][q]["rank"] for q in qs],
                      "rank_bottom": [preds[bot][q]["rank"] for q in qs]})
    json.dump({"rungs": have, "videos": index}, open(os.path.join(a.out, "index.json"), "w"), indent=1)
    print(f"wrote {len(index)} videos to {a.out}/  tags: {dict(Counter(tags[v] for v in picks))}")
    tot = sum(os.path.getsize(os.path.join(a.out, f)) for f in os.listdir(a.out))
    print(f"total size {tot/1e6:.2f} MB")


if __name__ == "__main__":
    main()
