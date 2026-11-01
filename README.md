# Reading Physics Through Relations: interactive demo

Open `index.html` in any browser (no server needed). Pick a scene, choose a forecast query,
and switch the relational vocabulary rung to see how the collision forecast changes.

- Scenes: 24 CLEVRER test videos, grouped as *vocabulary helps*, *long horizon*, *failure*, *occlusion*.
- Model: a fully inductive temporal knowledge-graph reasoner; no test object is seen in training.
- Facts are built from ground-truth CLEVRER states (no perception in the loop).

## Rebuilding
1. `scripts/clevrer_to_tkg.py`: convert CLEVRER annotations to temporal KG facts (four vocabulary rungs).
2. `scripts/physt_karma.py --dump-preds`: train and save per-query candidate scores.
3. `scripts/export_demo.py`: join predictions, facts and trajectories into per-scene JSON.
4. `scripts/build_demo.py`: inline everything into `index.html`.

Data: CLEVRER (Yi et al., ICLR 2020), http://clevrer.csail.mit.edu/
