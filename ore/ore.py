"""「俺」の字のオブジェ (Bambu Lab A1 mini 向け)

字の形を押し出し、下に台座の帯を付けて、離れた部首 (亻と奄) をつないでいる。
立てて飾る。STL は字の面を下にした向きで書き出してあり、サポートなしで印刷できる。
字形は Noto Sans JP (SIL Open Font License) を使い、初回に .cache へダウンロードする。

使い方: python ore.py -o stl/ore.stl
"""
import argparse
import struct
import urllib.request
from pathlib import Path

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from manifold3d import CrossSection, FillRule, Manifold

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf"
FONT_CACHE = Path(__file__).resolve().parent.parent / ".cache" / "NotoSansJP[wght].ttf"

# --- パラメータ ---
CHAR = "俺"
WEIGHT = 700      # 字の太さ (100〜900)。細いと折れやすい
HEIGHT = 70.0     # 字の高さ (台座を除く)
THICK = 18.0      # 字の厚み (立てたときの奥行き)
BASE_H = 5.0      # 台座の帯の高さ
BASE_PAD = 2.0    # 台座の帯を字の左右にはみ出させる長さ
CURVE_STEPS = 12  # 曲線 1 本を何本の線分で近似するか


class FlattenPen(BasePen):
    """グリフの輪郭を折れ線の点列にする"""

    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.contours = []
        self.cur = []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = np.array(self.cur[-1])
        for t in np.linspace(0, 1, CURVE_STEPS + 1)[1:]:
            q = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * np.array(p1) + 3 * (1 - t) * t**2 * np.array(p2) + t**3 * np.array(p3)
            self.cur.append(tuple(q))

    def _qCurveToOne(self, p1, p2):
        p0 = np.array(self.cur[-1])
        for t in np.linspace(0, 1, CURVE_STEPS + 1)[1:]:
            q = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * np.array(p1) + t**2 * np.array(p2)
            self.cur.append(tuple(q))

    def _closePath(self):
        if len(self.cur) >= 3:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


def load_font():
    if not FONT_CACHE.exists():
        FONT_CACHE.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {FONT_URL}")
        urllib.request.urlretrieve(FONT_URL, FONT_CACHE)
    font = TTFont(FONT_CACHE)
    return instantiateVariableFont(font, {"wght": WEIGHT})


def glyph_shape(font, char):
    glyph_set = font.getGlyphSet()
    pen = FlattenPen(glyph_set)
    glyph_set[font.getBestCmap()[ord(char)]].draw(pen)
    return CrossSection(pen.contours, FillRule.NonZero)


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


parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("-o", "--output", default="ore.stl")
args = parser.parse_args()

shape = glyph_shape(load_font(), CHAR)
x0, y0, x1, y1 = shape.bounds()
s = HEIGHT / (y1 - y0)
shape = shape.translate([-x0, -y0]).scale([s, s])
w = (x1 - x0) * s

# 台座の帯: 字の下端に少し重ねて、離れた部首をつなぐ
base = CrossSection.square([w + 2 * BASE_PAD, BASE_H + 1.0]).translate([-BASE_PAD, -BASE_H])
shape = shape + base

parts = len(shape.decompose())
if parts != 1:
    print(f"warning: 字が {parts} 個に分かれています (台座の帯につながっていない部分があります)")

body = Manifold.extrude(shape, THICK)
bb = body.bounding_box()
body = body.translate([-bb[0], -bb[1], -bb[2]])

write_stl(body, args.output)
bb = body.bounding_box()
print(f"size (print orientation): {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm")
print(f"volume: {body.volume()/1000:.1f} cm3, genus: {body.genus()}, parts: {parts}")
