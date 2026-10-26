"""STL を 4 方向から描いた PNG を作る。使い方: python preview.py in.stl out.png"""
import sys, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
d = np.fromfile(sys.argv[1], dtype=np.uint8)[84:]
rec = np.dtype([("n","<3f4"),("v","<9f4"),("a","<u2")])
t = np.frombuffer(d.tobytes(), dtype=rec)["v"].reshape(-1,3,3).copy()
# 印刷向き (前面が下) から使用向き (天板側が上) に戻す
x, y, z = t[...,0], t[...,1], t[...,2]
t = np.stack([x, z, y], -1)  # (x, depth, up)
t[...,0] -= t[...,0].mean()
views = [(25, -60, "iso"), (-25, -60, "from below"), (0, -90, "front"), (0, 0, "side")]
fig = plt.figure(figsize=(16, 12))
light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
n = np.cross(t[:,1]-t[:,0], t[:,2]-t[:,0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
shade = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
cols = np.stack([shade*0.30, shade*0.55, shade*0.85, np.ones_like(shade)], -1)
for i, (el, az, title) in enumerate(views):
    ax = fig.add_subplot(2, 2, i+1, projection="3d")
    ax.add_collection3d(Poly3DCollection(t, facecolors=cols, edgecolors="none"))
    mn, mx = t.reshape(-1,3).min(0), t.reshape(-1,3).max(0)
    c = (mn+mx)/2; r = (mx-mn).max()/2
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.set_box_aspect((1,1,1)); ax.view_init(el, az); ax.set_axis_off(); ax.set_title(title)
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=80)
