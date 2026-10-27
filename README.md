# 3d-models

3D プリンターで印刷するモデルの置き場です。モデルはどれも Python ([manifold3d](https://github.com/elalish/manifold)) のスクリプトで作っています。STL はスクリプトから作り直せます。

| モデル | 内容 |
| --- | --- |
| [anker-powerexpand-elite-holder](anker-powerexpand-elite-holder/) | Anker PowerExpand Elite 13-in-1 をデスクの天板の裏に取り付けるホルダー |
| [ore](ore/) | 「俺」の字のオブジェ |
| [ipad-pro-11-tray](ipad-pro-11-tray/) | iPad Pro 11 インチ (M4) を机の下にしまうトレー |
| [desk-audio-hanger](desk-audio-hanger/) | イヤホンのケースとヘッドホンを、充電しながら机の下に掛けておくハンガー |

## STL の作り直し方

```sh
make setup   # .venv を作って依存パッケージを入れる
make         # すべてのモデルの STL とプレビュー画像を作り直す
```

## 使っているプリンター

Bambu Lab A1 mini (造形サイズ 180 × 180 × 180 mm)
