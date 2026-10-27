"""iPad Pro 11 インチ (M4) を机の下にしまうトレー (Bambu Lab A1 mini 向け)

断面がコの字のトレーで、底板に iPad を寝かせ、上の板を両面テープで天板の裏に貼る。
iPad の幅 (249.7 mm) は A1 mini の造形範囲 (180 mm) に収まらないので、トレーを左右の半分に分けている。
左右の底板は真ん中の蟻継ぎ (台形の凸と溝) でつなぐ。右の半分を前から滑り込ませると、左右にも上下にも外れない。
蟻継ぎのところだけ、底板の下に背骨のような出っ張りがある。iPad の通り道には何も出っ張らない。
iPad は前から差し込み、奥の抜け止めで止まる。手前は少しはみ出して、つかんで引き出せる。

使用時の座標: X=左右 (X=0 がトレーの真ん中), Y=前後 (Y=0 が手前), Z=上 (天板の裏が Z 最大)
STL は左右の半分を前後に並べ、手前の面を下にした向きで書き出してあり、サポートなしで印刷できる。

使い方: python tray.py -o stl/tray.stl
        python tray.py --assembled -o assembled.stl  (組んだ状態。プレビュー用)
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
INNER_H = 20.0  # 底板の上面から上の板の下面までの高さ (ケースを付けても入るように)
LENGTH = 170.0  # トレーの奥行き (iPad の手前が少しはみ出す)
WALL = 3.0      # 横の壁の厚さ
FLOOR_T = 4.0   # 底板の厚さ
SPINE_D = 10.0  # 真ん中の背骨が底板の下に出る深さ
SPINE_W = 14.0  # 背骨の片側の幅 (真ん中からの距離)
DT_NECK = 4.0   # 蟻継ぎの凸の首の太さ
DT_NECK_L = 2.0 # 首の長さ
DT_HEAD = 9.0   # 凸の頭の太さ (首から 45° で広がる)
DT_L = 8.0      # 凸の長さ (首から頭の先まで)
DT_GAP = 0.25   # 蟻継ぎのすき間 (きついときは増やす)
TAB_T = 3.0     # 上の板の厚さ
TAB_W = 25.0    # 上の板の張り出し (両面テープを貼る幅)
STOP_H = 3.0    # 奥の抜け止めの高さ
STOP_L = 3.0    # 抜け止めの奥行き (この手前に 45° の斜面を付ける)
SLOT_W = 8.0    # 底板の肉抜きスリットの幅
SLOT_RIB = 5.0  # スリットどうしの間の骨の太さ
SLOT_END = 20.0 # スリットの端から前後端までの距離
R_OUT = 3.0     # 外側の角の丸み
R_IN = 1.0      # 内側の角の丸み (左右のすき間より大きくすると iPad の角に当たる)
GAP = 10.0      # 印刷するときの部品どうしの間隔
SEG = 48

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("-o", "--output", default="tray.stl")
parser.add_argument("--assembled", action="store_true", help="左右を組んだ状態で書き出す (プレビュー用)")
args = parser.parse_args()

inner_w = IPAD_W + CLEAR_W
iw = inner_w / 2
total_h = FLOOR_T + INNER_H + TAB_T
half_t = FLOOR_T / 2


def rect(xa, xb, z0, z1):
    """x は xa と xb のどちらが大きくてもよい"""
    x0, x1 = sorted((xa, xb))
    return CrossSection.square([x1 - x0, z1 - z0]).translate([x0, z0])


def poly(pts):
    """頂点の回り順を気にせず多角形を作る"""
    cs = CrossSection([pts])
    return cs if cs.area() > 0 else CrossSection([pts[::-1]])


def round_convex(cs, r):
    return cs.offset(-r, JoinType.Round, 2.0, SEG).offset(r, JoinType.Round, 2.0, SEG)


def round_concave(cs, r):
    return cs.offset(r, JoinType.Round, 2.0, SEG).offset(-r, JoinType.Round, 2.0, SEG)


def stadium(p0, p1, w):
    c = CrossSection.circle(w / 2, SEG)
    return CrossSection.batch_hull([c.translate(p0), c.translate(p1)])


def union(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out + s
    return out


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


def half_tray(side):
    """side=-1 で左、+1 で右の半分"""
    xw = side * iw                    # 壁の内側の面
    xo = side * (iw + WALL)           # 壁の外側の面
    xt = side * (iw - TAB_W)          # 上の板の先

    # ---------- 正面から見た断面 (XZ) ----------
    prof = rect(xo, xw, 0, total_h)                       # 横の壁
    prof = prof + rect(xo, 0, 0, FLOOR_T)                 # 底板 (真ん中まで)
    prof = prof + rect(xo, xt, total_h - TAB_T, total_h)  # 上の板
    prof = round_convex(round_concave(prof, R_IN), 1.0)
    # 外側の 2 つの角を大きめに丸める (真ん中側は相手とつなぐので丸めない)
    far = -side * 50
    outline = rect(xo - side * R_OUT, far, R_OUT, total_h - R_OUT).offset(R_OUT, JoinType.Round, 2.0, SEG)
    prof = prof ^ (outline + rect(xw, far, -SPINE_D - 1, total_h + 1))
    # 真ん中の背骨: 底板の下に出し、外側の下の角は 45° に落とす
    zb = -SPINE_D
    prof = prof + poly([(0, FLOOR_T), (0, zb), (side * (SPINE_W - SPINE_D / 2), zb),
                        (side * (SPINE_W + SPINE_D / 2), 0), (side * (SPINE_W + SPINE_D / 2), FLOOR_T)])
    # 蟻継ぎ: 左の半分に凸、右の半分に溝。凸は細い首から 45° で広がる頭を持つ
    zc = (zb + FLOOR_T) / 2

    def dovetail(grow):
        n, h = DT_NECK / 2 + grow, DT_HEAD / 2 + grow
        x_flare = DT_NECK_L + (DT_HEAD - DT_NECK) / 2  # 頭が太さいっぱいになる位置
        return poly([(-grow, zc - n), (DT_NECK_L, zc - n), (x_flare, zc - h), (DT_L + grow, zc - h),
                     (DT_L + grow, zc + h), (x_flare, zc + h), (DT_NECK_L, zc + n), (-grow, zc + n)])

    if side < 0:
        prof = prof + dovetail(0)
    else:
        prof = prof - dovetail(DT_GAP)

    # XZ 断面を Y 方向へ押し出す
    body = Manifold.extrude(prof, LENGTH).rotate([90, 0, 0]).translate([0, LENGTH, 0])

    # 底板の肉抜き: 前後に長いスリット (印刷時は縦長になるので、ブリッジは丸い端だけ)
    b0, b1 = sorted((xw - side * 8, side * (SPINE_W + SPINE_D / 2 + 4)))
    n = max(1, int((b1 - b0 + SLOT_RIB) // (SLOT_W + SLOT_RIB)))
    first = (b0 + b1) / 2 - (n * SLOT_W + (n - 1) * SLOT_RIB) / 2 + SLOT_W / 2
    slots = union([stadium((first + i * (SLOT_W + SLOT_RIB), SLOT_END + SLOT_W / 2),
                           (first + i * (SLOT_W + SLOT_RIB), LENGTH - SLOT_END - SLOT_W / 2), SLOT_W)
                   for i in range(n)])
    body = body - Manifold.extrude(slots, FLOOR_T + 2).translate([0, 0, -1])

    # 奥の抜け止め: 手前側を 45° の斜面にして、印刷時の張り出しをなくす。
    # 真ん中の継ぎ目の上には付けない (相手とぶつからないように)
    x0, x1 = sorted((xw - side * R_IN, side * (DT_L + DT_GAP + 0.5)))
    body = body + Manifold.hull_points([
        (x, y, z)
        for x in (x0, x1)
        for y, z in ((LENGTH - STOP_L - STOP_H, FLOOR_T - 0.5), (LENGTH, FLOOR_T - 0.5),
                     (LENGTH - STOP_L, FLOOR_T + STOP_H), (LENGTH, FLOOR_T + STOP_H))
    ])
    return body


left, right = half_tray(-1), half_tray(1)

# 組んだときにぶつからないか確かめる
overlap = (left ^ right).volume()
if overlap > 1e-3:
    print(f"warning: 左右が {overlap:.1f} mm3 ぶつかっています")

# ---------- 書き出し: 左右を前後に並べ、手前の面 (Y=0) を下にする ----------
printed = None
y = 0.0
for part in ([left + right] if args.assembled else (left, right)):
    p = part.rotate([-90, 0, 0])
    b = p.bounding_box()
    p = p.translate([-b[0], y - b[1], -b[2]])
    y += b[4] - b[1] + GAP
    printed = p if printed is None else printed + p

write_stl(printed, args.output)
bb, ab = printed.bounding_box(), (left + right).bounding_box()
print(f"size (print orientation): {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm")
print(f"assembled: {ab[3]-ab[0]:.1f} x {ab[4]-ab[1]:.1f} x {ab[5]-ab[2]:.1f} mm")
print(f"volume: {printed.volume()/1000:.1f} cm3, status: {printed.status()}")
print(f"inner width: {inner_w:.1f} mm, height above floor: {INNER_H:.1f} mm")
