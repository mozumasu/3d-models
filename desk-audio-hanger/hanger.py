"""イヤホンのケースとヘッドホンを、充電しながら机の下に掛けておくハンガー (Bambu Lab A1 mini 向け)

部品は 3 種類あり、--part で選ぶ。どれも両面テープで貼る。
  hanger: 天板の裏に貼る。左がイヤホンのケースを立てて入れるポケット、右がヘッドホンを掛けるフック。
          ケースは充電口を下にして立て、底の真ん中の前後に抜けたすき間にケーブルを前から通す。
  cradle: 充電器 (エレコム EC-AC12945) の下の面に貼り、充電器の真下にケースを寝かせて置く棚。
          ケースは充電口を手前に向けて寝かせ、手前からケーブルを差す。手前の低い縁で前へすべり出ない。
  hook:   天板の裏に貼る、ヘッドホンを掛けるフックだけ。cradle と組み合わせて使う。

hanger のポケットは、ケースを前から斜めに入れて底に立てる。手前の下のほうに渡した棒で、前へ倒れ出ないようにする。
フックは、壁の下から横に伸びる腕の先が上に折れていて、ヘッドバンドが抜けない。

使用時の座標: X=左右, Y=前後 (Y=0 が手前), Z=上 (貼る面が Z 最大)
STL は奥の面を下にした向きで書き出す。正面から見た形をそのまま積み上げるだけなので、サポートは要らない。
手前の棒と縁は左右の壁の間に渡したブリッジになる。

使い方: python hanger.py --part hanger -o stl/hanger.stl
        python hanger.py --part cradle -o stl/cradle.stl
        python hanger.py --part hook -o stl/hook.stl
"""
import argparse
import struct

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

# --- イヤホンのケースの寸法 (カバーを付けた状態で測って直す) ---
CASE_W = 64.0   # 幅 (充電口のある面の長いほうの辺)
CASE_T = 25.0   # 厚さ
CASE_H = 50.0   # 高さ (充電口のある面からふたの上まで)

# --- パラメータ ---
CLEAR = 1.5     # ケースとのすき間 (幅と厚さ、それぞれ合計)
WALL = 3.0      # 左右の壁の厚さ
FLOOR_T = 3.0   # 底の厚さ
PLATE_T = 3.0   # 貼る板の厚さ
BACK_T = 2.5    # 奥の板の厚さ
WINDOW = 8.0    # 奥の板の窓のふちの幅
CABLE_W = 14.0  # hanger: 底の真ん中の、ケーブルのプラグを通すすき間の幅
SILL_H = 5.0    # cradle: 手前の縁の高さ (底の上面から)。ケースの充電口より低くする
SILL_LIFT = 2.0 # cradle: ケースを縁の上まで持ち上げて出し入れするときの余裕
BAR_Z0 = 6.0    # 手前の棒の下の端 (底の上面から)。hanger ではこの下からケーブルを通す
BAR_Z1 = 14.0   # 手前の棒の上の端
BAR_T = 3.0     # 手前の棒の厚さ
LIFT = 4.0      # hanger: ケースを棒の上まで持ち上げて出し入れするときの余裕
ARM = 35.0      # フックの腕の長さ (壁の外から先まで)
ARM_T = 6.0     # 腕の太さ
LIP_H = 14.0    # 腕の先の折れ上がりの高さ
LIP_T = 5.0     # 折れ上がりの厚さ
HOOK_H = 45.0   # hook: 貼る面から腕の下の面までの高さ
HOOK_D = 30.0   # hook: 奥行き
R_FIL = 6.0     # 腕と壁、板と壁の間の丸み
R_OUT = 1.5     # 外側の角の丸み
R_IN = 0.7      # ポケットの内側の角の丸み (左右のすき間より大きくするとケースの角に当たる)
SEG = 48

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--part", choices=["hanger", "cradle", "hook"], default="hanger")
parser.add_argument("-o", "--output", default="hanger.stl")
args = parser.parse_args()

iw = (CASE_W + CLEAR) / 2         # ポケットの内側の半分の幅
ow = iw + WALL                    # 外側の半分の幅
if args.part == "cradle":
    # ケースを寝かせる: 前後がケースの高さ、上下がケースの厚さ。手前の棒は底から立ち上がる低い縁にする
    case_d, inner_h, bar_z0, bar_z1 = CASE_H, CASE_T + SILL_H + SILL_LIFT, -0.01, SILL_H
else:
    # ケースを立てる: 前後がケースの厚さ、上下がケースの高さ
    case_d, inner_h, bar_z0, bar_z1 = CASE_T, CASE_H + BAR_Z1 + LIFT, BAR_Z0, BAR_Z1
z_plate = FLOOR_T + inner_h       # 貼る板の下面
total_h = z_plate + PLATE_T
depth = BAR_T + case_d + CLEAR + BACK_T


def rect(xa, xb, z0, z1):
    """x は xa と xb のどちらが大きくてもよい"""
    x0, x1 = sorted((xa, xb))
    return CrossSection.square([x1 - x0, z1 - z0]).translate([x0, z0])


def rounded_rect(x0, x1, z0, z1, r):
    return rect(x0 + r, x1 - r, z0 + r, z1 - r).offset(r, JoinType.Round, 2.0, SEG)


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def extrude_y(prof, y0, y1):
    """XZ 断面を Y 方向 y0..y1 に押し出す"""
    return Manifold.extrude(prof, y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def smooth(prof):
    """へこんだ角を丸めてから、出っ張った角を丸める"""
    prof = prof.offset(R_FIL, JoinType.Round, 2.0, SEG).offset(-R_FIL, JoinType.Round, 2.0, SEG)
    return prof.offset(-R_OUT, JoinType.Round, 2.0, SEG).offset(R_OUT, JoinType.Round, 2.0, SEG)


def hook_arm(x0):
    """x0 から右へ伸びる腕と、先の折れ上がり (正面から見た形)"""
    x_tip = x0 + ARM
    return rect(x0 - 1, x_tip, 0, ARM_T) + rect(x_tip - LIP_T, x_tip, 0, LIP_H)


def pocket(with_hook):
    """ケースを入れるポケット。with_hook で右の壁にフックを付ける"""
    x_right = ow + ARM if with_hook else ow
    prof = rect(-ow, ow, 0, total_h) + rect(-ow, x_right, z_plate, total_h)
    if with_hook:
        prof = prof + hook_arm(ow)
    prof = smooth(prof)
    prof = prof - rounded_rect(-iw, iw, FLOOR_T, z_plate, R_IN)        # ポケットの中
    if args.part == "hanger":
        prof = prof - rect(-CABLE_W / 2, CABLE_W / 2, -1, FLOOR_T + 1)  # ケーブルを通すすき間
    body = extrude_y(prof, 0, depth)

    # 奥の板 (真ん中は窓にして軽くする)
    back = rect(-iw - 0.01, iw + 0.01, FLOOR_T - 0.01, z_plate + 0.01) - rounded_rect(
        -iw + WINDOW, iw - WINDOW, FLOOR_T + WINDOW, z_plate - WINDOW, 4.0)
    body = body + extrude_y(back, depth - BACK_T, depth)

    # 手前の棒 (cradle では低い縁)
    return body + box(-iw - 0.01, iw + 0.01, 0, BAR_T, FLOOR_T + bar_z0, FLOOR_T + bar_z1)


def hook():
    # 縦の柱と貼る板は腕と同じ太さにする (薄いと角を丸めるときに消える)
    top = HOOK_H + ARM_T
    prof = rect(0, ARM_T, 0, top) + rect(0, ARM_T + ARM, HOOK_H, top) + hook_arm(ARM_T)
    return extrude_y(smooth(prof), 0, HOOK_D)


body = hook() if args.part == "hook" else pocket(args.part == "hanger")

# ---------- 書き出し ----------
# 印刷向き: 奥の面 (Y 最大) を下に
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
print(f"{args.part}: size (print orientation): {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm")
print(f"volume: {printed.volume()/1000:.1f} cm3, genus: {printed.genus()}, status: {printed.status()}")
