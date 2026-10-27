"""iPad Pro 11 インチ (M4) を机の下にしまうレール (Bambu Lab A1 mini 向け)

iPad の幅 (249.7 mm) は A1 mini の造形範囲 (180 mm) に収まらないので、左右 2 本のレールに分けている。
レールは前後方向に伸び、iPad の左右のふちを下の棚で受ける。上の板を両面テープで天板の裏に貼る。
iPad は前から差し込み、奥の抜け止めで止まる。手前は少しはみ出して、つかんで引き出せる。

使用時の座標: X=左右, Y=前後 (Y=0 が手前), Z=上 (天板の裏が Z 最大)
STL は 2 本を並べ、断面を下にした向きで書き出してあり、サポートなしで印刷できる。

使い方: python rails.py -o stl/rails.stl
"""
import argparse
import struct

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

# --- iPad Pro 11 インチ (M4) の寸法 (Apple の仕様) ---
IPAD_W = 249.7
IPAD_D = 177.5
IPAD_T = 5.3

# --- パラメータ ---
CLEAR_W = 2.0   # 左右のすき間 (合計)
INNER_H = 20.0  # 棚の上面から上の板の下面までの高さ (ケースを付けても入るように)
LENGTH = 170.0  # レールの長さ (iPad の手前が少しはみ出す)
WALL = 3.0      # 横の壁の厚さ
SHELF_T = 3.0   # 下の棚の厚さ
SHELF_W = 15.0  # 下の棚の張り出し (iPad のふちに掛かる幅)
TAB_T = 3.0     # 上の板の厚さ
TAB_W = 25.0    # 上の板の張り出し (両面テープを貼る幅)
STOP_H = 3.0    # 奥の抜け止めの高さ
STOP_L = 3.0    # 抜け止めの奥行き (この手前に 45° の斜面を付ける)
R_OUT = 3.0     # 外側の角の丸み
R_IN = 1.5      # 内側の角の丸み
GAP = 10.0      # 印刷するときの 2 本の間隔
SEG = 48

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("-o", "--output", default="rails.stl")
args = parser.parse_args()

total_h = SHELF_T + INNER_H + TAB_T


def rect(x0, y0, x1, y1):
    return CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])


def round_convex(cs, r):
    return cs.offset(-r, JoinType.Round, 2.0, SEG).offset(r, JoinType.Round, 2.0, SEG)


def round_concave(cs, r):
    return cs.offset(r, JoinType.Round, 2.0, SEG).offset(-r, JoinType.Round, 2.0, SEG)


def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    with open(path, "wb") as f:
        f.write(b"\0" * 80)
        f.write(struct.pack("<I", len(t)))
        for a, b, c in t:
            p0, p1, p2 = v[a], v[b], v[c]
            n = np.cross(p1 - p0, p2 - p0)
            ln = np.linalg.norm(n)
            n = n / ln if ln else n
            f.write(struct.pack("<12fH", *n, *p0, *p1, *p2, 0))


# ---------- 左のレールの断面 (XZ)。x=0 が壁の内側の面、+X が iPad 側 ----------
prof = rect(-WALL, 0, 0, total_h)                                  # 横の壁
prof = prof + rect(-WALL, 0, SHELF_W, SHELF_T)                     # 下の棚
prof = prof + rect(-WALL, total_h - TAB_T, TAB_W, total_h)         # 上の板
prof = round_convex(round_concave(prof, R_IN), 1.0)                # 内側の角と、出っ張った角
outline = rect(-WALL + R_OUT, R_OUT, TAB_W - R_OUT, total_h - R_OUT).offset(R_OUT, JoinType.Round, 2.0, SEG)
prof = prof ^ outline                                              # 外側の四隅を大きめに丸める

# XZ 断面を Y 方向へ押し出す
rail = Manifold.extrude(prof, LENGTH).rotate([90, 0, 0]).translate([0, LENGTH, 0])

# 奥の抜け止め: 手前側を 45° の斜面にして、印刷時の張り出しをなくす
x0, x1 = R_IN, SHELF_W - 1.0
wedge = Manifold.hull_points([
    (x, y, z)
    for x in (x0, x1)
    for y, z in ((LENGTH - STOP_L - STOP_H, SHELF_T - 0.5), (LENGTH, SHELF_T - 0.5),
                 (LENGTH - STOP_L, SHELF_T + STOP_H), (LENGTH, SHELF_T + STOP_H))
])
rail = rail + wedge

# ---------- 書き出し: 左右 2 本を、手前の面 (Y=0) を下にして並べる ----------
left = rail.rotate([-90, 0, 0])
right = rail.mirror([1, 0, 0]).rotate([-90, 0, 0])
bl, br = left.bounding_box(), right.bounding_box()
left = left.translate([-bl[0], -bl[1], -bl[2]])
right = right.translate([-br[0] + (bl[3] - bl[0]) + GAP, -br[1], -br[2]])
printed = left + right

write_stl(printed, args.output)
bb = printed.bounding_box()
print(f"size (print orientation): {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm")
print(f"volume: {printed.volume()/1000:.1f} cm3, status: {printed.status()}")
print(f"rail spacing (inner wall to inner wall): {IPAD_W + CLEAR_W:.1f} mm")
