"""iPad Pro 11 インチ (M4) を机の下にしまうトレー (Bambu Lab A1 mini 向け)

断面がコの字のトレーで、底板に iPad を寝かせ、上の板を両面テープで天板の裏に貼る。
iPad の幅 (249.7 mm) は A1 mini の造形範囲 (180 mm) に収まらないので、左右のレールと真ん中の板の 3 つに分けている。

  レール: 横の壁、天板に貼る上の板、底板の外側の部分。底板は 2 段で、下の段が内側へ長く伸びて真ん中の板を受ける。
          上の段のふちには、蟻の形の切り欠きを並べてある。
  真ん中の板: 左右のふちに蟻の形の凸があり、上からレールにはめ込む。ふちの下側は段欠きにしてあり、レールの下の段に載る。
          はめると上面はレールと平らにそろい、左右にも前後にも外れない。

iPad は前から差し込み、奥の抜け止めで止まる。手前は少しはみ出して、つかんで引き出せる。

使用時の座標: X=左右 (X=0 がトレーの真ん中), Y=前後 (Y=0 が手前), Z=上 (天板の裏が Z 最大)
STL はレール 2 本 (手前の面を下にして並べる) と、真ん中の板 (上面を下にする) の 2 つに分けて書き出す。
どちらもサポートなしで印刷できる。

使い方: python tray.py --part rails -o stl/rails.stl
        python tray.py --part plate -o stl/plate.stl
        python tray.py --part assembled -o assembled.stl  (組んだ状態。プレビュー用)
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
FLOOR_T = 4.0   # 底板の厚さ (上の段と下の段で半分ずつ)
TAB_T = 3.0     # 上の板の厚さ
TAB_W = 25.0    # 上の板の張り出し (両面テープを貼る幅)
PLATE_W = 150.0 # 真ん中の板の上の段の幅 (凸を除く)。凸を含めて造形範囲に収める
LEDGE = 8.0     # レールの下の段が、上の段より内側へ伸びる長さ (真ん中の板を受ける幅)
DT_N = 4        # 片側の蟻の凸の数
DT_NECK = 8.0   # 凸の付け根の幅
DT_HEAD = 16.0  # 凸の先の幅 (付け根より広いので抜けない)
DT_DEPTH = 8.0  # 凸の長さ
DT_GAP = 0.2    # はめ合いのすき間 (きついときは増やす)
STOP_H = 3.0    # 奥の抜け止めの高さ
STOP_L = 3.0    # 抜け止めの奥行き (この手前に 45° の斜面を付ける)
SLOT_W = 8.0    # 真ん中の板の肉抜きスリットの幅
SLOT_RIB = 5.0  # スリットどうしの間の骨の太さ
SLOT_END = 20.0 # スリットの端から前後端までの距離
R_OUT = 3.0     # 外側の角の丸み
R_IN = 1.0      # 内側の角の丸み (左右のすき間より大きくすると iPad の角に当たる)
GAP = 10.0      # 印刷するときの部品どうしの間隔
SEG = 48

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--part", choices=["rails", "plate", "assembled"], default="rails")
parser.add_argument("-o", "--output", default="tray.stl")
args = parser.parse_args()

inner_w = IPAD_W + CLEAR_W
iw = inner_w / 2
total_h = FLOOR_T + INNER_H + TAB_T
half_t = FLOOR_T / 2
pe = PLATE_W / 2      # 真ん中の板の上の段のふち (= レールの上の段のふち)
le = pe - LEDGE       # レールの下の段の先 (= 真ん中の板の下の段のふち)


def rect(xa, xb, z0, z1):
    """x は xa と xb のどちらが大きくてもよい"""
    x0, x1 = sorted((xa, xb))
    return CrossSection.square([x1 - x0, z1 - z0]).translate([x0, z0])


def poly(pts):
    """頂点の回り順を気にせず多角形を作る"""
    cs = CrossSection([pts])
    return cs if cs.area() > 0 else CrossSection([pts[::-1]])


def union(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out + s
    return out


def round_convex(cs, r):
    return cs.offset(-r, JoinType.Round, 2.0, SEG).offset(r, JoinType.Round, 2.0, SEG)


def round_concave(cs, r):
    return cs.offset(r, JoinType.Round, 2.0, SEG).offset(-r, JoinType.Round, 2.0, SEG)


def stadium(p0, p1, w):
    c = CrossSection.circle(w / 2, SEG)
    return CrossSection.batch_hull([c.translate(p0), c.translate(p1)])


def extrude_y(prof):
    """XZ 断面を Y 方向 0..LENGTH に押し出す"""
    return Manifold.extrude(prof, LENGTH).rotate([90, 0, 0]).translate([0, LENGTH, 0])


def extrude_z(cs_xy, z0, z1):
    """XY の形を Z 方向 z0..z1 に押し出す"""
    return Manifold.extrude(cs_xy, z1 - z0).translate([0, 0, z0])


def dovetails(side, grow):
    """真ん中の板の side 側のふちの凸 (上から見た XY の形)。grow でふくらませると切り欠きになる"""
    pitch = LENGTH / DT_N
    x0, x1 = side * (pe - grow), side * (pe + DT_DEPTH + grow)
    shapes = []
    for i in range(DT_N):
        yc = pitch * (i + 0.5)
        n, h = DT_NECK / 2 + grow, DT_HEAD / 2 + grow
        shapes.append(poly([(x0, yc - n), (x1, yc - h), (x1, yc + h), (x0, yc + n)]))
    return union(shapes)


def rail(side):
    """side=-1 で左、+1 で右のレール"""
    xw = side * iw                    # 壁の内側の面
    xo = side * (iw + WALL)           # 壁の外側の面
    xt = side * (iw - TAB_W)          # 上の板の先

    prof = rect(xo, xw, 0, total_h)                          # 横の壁
    prof = prof + rect(xo, side * pe, 0, FLOOR_T)            # 底板 (上の段のふちまで)
    prof = prof + rect(xo, xt, total_h - TAB_T, total_h)     # 上の板
    prof = round_convex(round_concave(prof, R_IN), 0.5)
    # 底板の下の段 (真ん中の板を受ける)。段の角は板とぴったり合うように丸めない
    prof = prof + rect(side * (pe - 1), side * le, 0, half_t)
    # 外側の 2 つの角を大きめに丸める
    far = -side * (pe + 50)
    outline = rect(xo - side * R_OUT, far, R_OUT, total_h - R_OUT).offset(R_OUT, JoinType.Round, 2.0, SEG)
    prof = prof ^ (outline + rect(xw, far, -1, total_h + 1))
    body = extrude_y(prof)

    # 上の段の蟻の切り欠き (下の段は残して、凸を下から受ける)
    body = body - extrude_z(dovetails(side, DT_GAP), half_t, FLOOR_T + 1)

    # 奥の抜け止め: 手前側を 45° の斜面にして、印刷時の張り出しをなくす
    x0, x1 = sorted((xw - side * R_IN, side * (pe + DT_DEPTH + 2)))
    body = body + Manifold.hull_points([
        (x, y, z)
        for x in (x0, x1)
        for y, z in ((LENGTH - STOP_L - STOP_H, FLOOR_T - 0.5), (LENGTH, FLOOR_T - 0.5),
                     (LENGTH - STOP_L, FLOOR_T + STOP_H), (LENGTH, FLOOR_T + STOP_H))
    ])
    return body


def plate():
    g = DT_GAP
    upper = CrossSection.square([2 * (pe - g), LENGTH]).translate([-(pe - g), 0])
    upper = upper + dovetails(-1, 0) + dovetails(1, 0)
    lower = CrossSection.square([2 * (le - g), LENGTH]).translate([-(le - g), 0])
    body = extrude_z(upper, half_t, FLOOR_T) + extrude_z(lower, 0, half_t + 0.01)

    # 肉抜き: 前後に長いスリット
    b0, b1 = -(le - 8), le - 8
    n = max(1, int((b1 - b0 + SLOT_RIB) // (SLOT_W + SLOT_RIB)))
    first = (b0 + b1) / 2 - (n * SLOT_W + (n - 1) * SLOT_RIB) / 2 + SLOT_W / 2
    slots = union([stadium((first + i * (SLOT_W + SLOT_RIB), SLOT_END + SLOT_W / 2),
                           (first + i * (SLOT_W + SLOT_RIB), LENGTH - SLOT_END - SLOT_W / 2), SLOT_W)
                   for i in range(n)])
    return body - extrude_z(slots, -1, FLOOR_T + 1)


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


def to_bed(m):
    b = m.bounding_box()
    return m.translate([-b[0], -b[1], -b[2]])


left, right, center = rail(-1), rail(1), plate()

# 組んだときにぶつからないか確かめる
for name, a, b in (("左のレールと板", left, center), ("右のレールと板", right, center), ("左右のレール", left, right)):
    v = (a ^ b).volume()
    if v > 1e-3:
        print(f"warning: {name}が {v:.1f} mm3 ぶつかっています")

# ---------- 書き出し ----------
if args.part == "rails":
    # 2 本を、手前の面 (Y=0) を下にして前後に並べる
    out, y = None, 0.0
    for part in (left, right):
        p = part.rotate([-90, 0, 0])
        b = p.bounding_box()
        p = p.translate([-b[0], y - b[1], -b[2]])
        y += b[4] - b[1] + GAP
        out = p if out is None else out + p
elif args.part == "plate":
    # 上面を下にする (ふちの段欠きが宙に浮かないように)
    out = to_bed(center.rotate([180, 0, 0]))
else:
    out = (left + right + center).rotate([-90, 0, 0])

write_stl(out, args.output)
bb = out.bounding_box()
ab = (left + right + center).bounding_box()
print(f"{args.part}: size {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm, volume {out.volume()/1000:.1f} cm3")
print(f"assembled: {ab[3]-ab[0]:.1f} x {ab[4]-ab[1]:.1f} x {ab[5]-ab[2]:.1f} mm")
