"""Anker PowerExpand Elite 13-in-1 用 デスク下ホルダー (Bambu Lab A1 mini 向け)

使用時の座標: X=幅, Y=奥行き(前後にポート), Z=上 (天板の裏が Z 最大)
出力 STL は横倒し (前面を下) にしてあり、サポートなしで印刷できる。
斜めの形はすべて印刷時に 45° 以下になるようにしてある。
通気口のデザインは 2 種類から選べる。
  stripe:  前後方向に長い角丸スリット (すっきりした見た目)
  lattice: ひし形の格子 (トラス風で軽い)
取り付け方も 2 種類から選べる。
  screw: 左右のフランジを木ネジで天板の裏に留める
  tape:  フランジなし。天板側の板を穴のない平らな面にして、両面テープで貼る
--floor を付けると、下をレールではなく床でふさぐ (床にも通気口を開ける)。

使い方: python holder.py --style stripe -o stl/holder-stripe.stl
        python holder.py --mount tape --floor --wall 3.2 --rib 4 -o stl/holder-tape.stl
"""
import argparse
import struct

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

# --- ドック実寸 (実物を測って直す) ---
DOCK_W = 125.8
DOCK_D = 88.5
DOCK_H = 41.9

# --- パラメータ ---
CLEAR_W = 1.2   # 幅方向のすき間 (合計)
CLEAR_H = 1.2   # 高さ方向のすき間
CLEAR_D = 1.0   # 奥行き方向のすき間 (合計)
WALL = 2.6      # 側壁の厚さ
RAIL_T = 3.5    # 下のレールの厚さ
RAIL_W = 14.0   # 下のレールの張り出し
PLATE_T = 4.0   # 天板に当たる板の厚さ
FLANGE = 16.0   # ネジ止めフランジの張り出し
TAB_L = 32.0    # フランジは前後端のこの長さだけ残す (根元の長さ)
HOLE_Y = 14.0   # ネジ穴の前後端からの位置
STOP_H = 2.0    # 前後の抜け止めの高さ (0 で無し)
STOP_L = 3.0    # 抜け止めの長さ
SCREW_D = 4.5   # ネジ穴 (4mm 木ネジ想定)
CSK_D = 9.0     # 皿ザグリ径
R_OUT = 5.0     # 外側の下の角の丸み
R_IN = 1.5      # ドックが入る内側の角の丸み
R_FILLET = 4.0  # 側壁とフランジのつなぎ目の丸み
R_EDGE = 1.0    # そのほかの角の丸み
TAB_CHAMFER = 3.0  # タブの先の角の面取り
SLOT_W = 5.0    # 側壁とレールのスリットの幅
PLATE_SLOT_W = 6.0  # 天板側の板のスリットの幅
SLOT_RIB = 3.0  # スリットどうしの間の骨の太さ
SLOT_END = 9.0  # スリットの端から前後端までの距離
VENT_H = 9.0    # ひし形の中心から頂点まで (lattice)
VENT_RIB = 2.2  # ひし形どうしの間の骨の太さ (lattice)
TAPE_SKIN = 1.6 # テープで貼るとき、天板側の板の貼る面に残す厚さ
SEG = 64

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--style", choices=["stripe", "lattice"], default="stripe")
parser.add_argument("--mount", choices=["screw", "tape"], default="screw")
parser.add_argument("--floor", action="store_true", help="下を床でふさぐ")
parser.add_argument("--wall", type=float, default=WALL, help="側壁の厚さ")
parser.add_argument("--rib", type=float, default=SLOT_RIB, help="スリットどうしの間の骨の太さ (stripe)")
parser.add_argument("-o", "--output", default="holder.stl")
args = parser.parse_args()
WALL, SLOT_RIB = args.wall, args.rib
screw = args.mount == "screw"

inner_w = DOCK_W + CLEAR_W
inner_h = DOCK_H + CLEAR_H
stop_l = STOP_L if STOP_H > 0 else 0.0
depth = DOCK_D + CLEAR_D + 2 * stop_l
outer_w = inner_w + 2 * WALL
z_plate = RAIL_T + inner_h
total_h = z_plate + PLATE_T
total_w = outer_w + 2 * FLANGE if screw else outer_w
ow, iw = outer_w / 2, inner_w / 2


def rect(x0, y0, x1, y1):
    return CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])


def rounded_rect(x0, y0, x1, y1, r):
    return rect(x0 + r, y0 + r, x1 - r, y1 - r).offset(r, JoinType.Round, 2.0, SEG)


def poly(pts):
    """頂点の回り順を気にせず多角形を作る"""
    cs = CrossSection([pts])
    return cs if cs.area() > 0 else CrossSection([pts[::-1]])


def union(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out + s
    return out


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def stadium(p0, p1, w):
    c = CrossSection.circle(w / 2, SEG)
    return CrossSection.batch_hull([c.translate(p0), c.translate(p1)])


# ---------- 正面から見た断面 (XZ) ----------
# 外形: 外側の下の角だけ大きく丸める
prof = rounded_rect(-ow, 0, ow, total_h + R_OUT, R_OUT) ^ rect(-ow, 0, ow, total_h)
prof = prof + rect(-total_w / 2, z_plate, total_w / 2, total_h)
# 側壁とフランジの間を丸くつなぐ
for sx in ((-1, 1) if screw else ()):
    cx = sx * (ow + R_FILLET)
    corner = rect(min(sx * ow, cx), z_plate - R_FILLET, max(sx * ow, cx), z_plate)
    prof = prof + (corner - CrossSection.circle(R_FILLET, SEG).translate([cx, z_plate - R_FILLET]))
# ドックが入る空間と、下の開口
prof = prof - rounded_rect(-iw, RAIL_T, iw, z_plate, R_IN)
if not args.floor:
    prof = prof - rect(-(iw - RAIL_W), -1, iw - RAIL_W, RAIL_T + R_IN)
# 残りの角を軽く丸める (opening: 出っ張った角だけが丸くなる)
prof = prof.offset(-R_EDGE, JoinType.Round, 2.0, SEG).offset(R_EDGE, JoinType.Round, 2.0, SEG)

# XZ 断面を Y 方向へ押し出す (XY で作って X 軸回りに回すと Y が Z になる)
body = Manifold.extrude(prof, depth).rotate([90, 0, 0]).translate([0, depth, 0])

# ---------- フランジを前後端のタブだけにする (上から見て 45° に絞る) ----------
for sx in ((-1, 1) if screw else ()):
    x0, x1 = sx * ow, sx * (total_w / 2 + 1)
    run = abs(x1 - x0)
    cuts = [poly([(x0, TAB_L), (x1, TAB_L - run), (x1, depth - TAB_L + run), (x0, depth - TAB_L)])]
    # タブの先の角も 45° で落とす
    xt, c = sx * total_w / 2, TAB_CHAMFER
    for y, dy in ((0, 1), (depth, -1)):
        cuts.append(poly([(xt - sx * c, y - dy), (xt + sx, y - dy), (xt + sx, y + dy * (c + 1))]))
    body = body - Manifold.extrude(union(cuts), total_h + 2).translate([0, 0, -1])

# ---------- 抜け止め (レールの前後端だけ) ----------
if STOP_H > 0:
    for sx in (-1, 1):
        xa, xb = sorted((sx * (iw - 1.5), sx * (iw - RAIL_W + 1.5)))
        for y0 in (0, depth - stop_l):
            body = body + box(xa, y0, RAIL_T - 0.5, xb, y0 + stop_l, RAIL_T + STOP_H)

# ---------- ネジ穴 (下から皿ネジで天板裏へ) ----------
hole_x = ow + FLANGE / 2
csk_h = (CSK_D - SCREW_D) / 2
for sx in ((-1, 1) if screw else ()):
    for y in (HOLE_Y, depth - HOLE_Y):
        body = body - Manifold.cylinder(PLATE_T + 2, SCREW_D / 2, SCREW_D / 2, SEG).translate([sx * hole_x, y, z_plate - 1])
        body = body - Manifold.cylinder(csk_h + 0.01, CSK_D / 2, SCREW_D / 2, SEG).translate([sx * hole_x, y, z_plate - 0.01])


# ---------- 通気口 ----------
def wall_cutter(cs_ab, t0, t1):
    """(a=Y, b=Z) の 2D を X 方向 t0..t1 に押し出す"""
    return Manifold.extrude(cs_ab, t1 - t0).transform([[0, 0, 1, t0], [1, 0, 0, 0], [0, 1, 0, 0]])


def flat_cutter(cs_ab, z0, z1):
    """(a=Y, b=X) の 2D を Z 方向 z0..z1 に押し出す"""
    return Manifold.extrude(cs_ab, z1 - z0).transform([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, -1, z1]])


# stripe: 前後方向に長い角丸スリット。印刷時は縦長になるので、ブリッジは丸い端の小さな半円だけで済む
def stripe_slots(a0, a1, b0, b1, w, rib):
    """a=前後(Y) に長いスリットを、b 方向に w+rib 間隔で中央そろえに並べる"""
    n = max(1, int((b1 - b0 + rib) // (w + rib)))
    used = n * w + (n - 1) * rib
    first = (b0 + b1) / 2 - used / 2 + w / 2
    return union([stadium((a0 + w / 2, first + i * (w + rib)), (a1 - w / 2, first + i * (w + rib)), w) for i in range(n)])


# lattice: ひし形の格子。印刷時の上下 (使用時の前後 = Y) に頂点を向けるので 45° の斜面だけになる
def diamond_lattice(a0, a1, b0, b1):
    pitch = 2 * VENT_H + VENT_RIB * 2 ** 0.5
    out = []
    for row in range(-50, 50):
        for col in range(-50, 50):
            a = (a0 + a1) / 2 + (col + (row % 2) / 2) * pitch
            b = (b0 + b1) / 2 + row * pitch / 2
            # 前後 (a) ははみ出さないものだけ、幅 (b) ははみ出す分を切り落とす
            if a0 + VENT_H <= a <= a1 - VENT_H and b0 - VENT_H < b < b1 + VENT_H:
                out.append(poly([(a + VENT_H, b), (a, b + VENT_H), (a - VENT_H, b), (a, b - VENT_H)]))
    return union(out) ^ rect(a0, b0, a1, b1)


if args.style == "stripe":
    wall_vents = stripe_slots(SLOT_END, depth - SLOT_END, RAIL_T + 3, z_plate - 3, SLOT_W, SLOT_RIB)
    plate_vents = stripe_slots(SLOT_END, depth - SLOT_END, -iw + 4, iw - 4, PLATE_SLOT_W, SLOT_RIB)
    rail_vents = lambda b0, b1: stripe_slots(stop_l + SLOT_END, depth - stop_l - SLOT_END, b0, b1, SLOT_W, SLOT_RIB)
else:
    wall_vents = diamond_lattice(4, depth - 4, RAIL_T + 2, z_plate - 2)
    plate_vents = diamond_lattice(4, depth - 4, -iw + 3, iw - 3)
    rail_vents = lambda b0, b1: diamond_lattice(stop_l + 3, depth - stop_l - 3, b0, b1)

# 側壁
for sx in (-1, 1):
    t0, t1 = sorted((sx * (iw - 0.5), sx * (ow + 1)))
    body = body - wall_cutter(wall_vents, t0, t1)
# 天板側の板 (テープで貼るときは、貼る面を平らに残して内側だけ肉抜きする)
if screw:
    body = body - flat_cutter(plate_vents, z_plate - 1, total_h + 1)
else:
    body = body - flat_cutter(plate_vents, z_plate - 1, total_h - TAPE_SKIN)
# 下のレールか床
if args.floor:
    body = body - flat_cutter(rail_vents(-iw + 3, iw - 3), -1, RAIL_T + 1)
else:
    for sx in (-1, 1):
        b0, b1 = sorted((sx * (iw - 2), sx * (iw - RAIL_W + 2)))
        body = body - flat_cutter(rail_vents(b0, b1), -1, RAIL_T + 1)

# ---------- 書き出し ----------
# 印刷向き: 前面 (Y=0) を下に
printed = body.rotate([-90, 0, 0])
bb = printed.bounding_box()
printed = printed.translate([-bb[0], -bb[1], -bb[2]])


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


write_stl(printed, args.output)
bb = printed.bounding_box()
print(f"{args.style}/{args.mount}{'/floor' if args.floor else ''}: size (print orientation): {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm")
print(f"volume: {printed.volume()/1000:.1f} cm3, genus: {printed.genus()}, status: {printed.status()}")
