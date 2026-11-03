"""自定义页语言那一行：五项单选「中文 / English / Español / Русский / 한국어」的跨语言契约。
语言行的控件名、勾选框列位置、五个选项各自的正文字宽与宿主 dm_custom.c 的表必须一致——五项已占满这一行（标签字让掉了），
所以位置是硬编码的，改一行字就要回来量这里。"""
import json, re, sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'ios/tools'))
import touch_layout as layout

out, _ = layout._custom_page('"name": "VideoOptionsPanel", "name": "OptionsTable"')
page = json.loads(re.sub(r',\s*([}\]])', r'\1', out))
nodes = {}
def walk(node):
    if isinstance(node, dict):
        if 'name' in node:
            assert node['name'] not in nodes, node['name']
            nodes[node['name']] = node
        for child in node.values():
            walk(child)
    elif isinstance(node, list):
        for child in node:
            walk(child)
walk(page)

opts = (('zh', 'Zh', 'dmCustomLangZh', 0), ('en', 'En', 'dmCustomLangEnOpt', 0), ('es', 'Es', 'dmCustomLangEsOpt', 0), ('ru', 'Ru', 'dmCustomLangRuOpt', 0),
        ('ko', 'Ko', 'dmCustomLangKoOpt', 0), ('de', 'De', 'dmCustomLangDeOpt', 1))
for key, cap, label, _ in opts:
    box = nodes['TouchCustom_lang_' + key]
    assert box['type'] == 'ToggleButtonWidget', key
    assert box['fields']['onClickMessage'].endswith('TouchCustom_lang_' + key), key
    assert nodes['TouchCustomLang%s_Text' % cap]['fields']['text'] == '@' + label, key
    assert nodes['TouchCustomLangHint%s' % cap]['fields']['text'] == '@dmCustomLangHint' + cap, key
    assert nodes['TouchCustomLangHint%s' % cap]['fields']['rect']['x'] > 10000, 'hint starts off screen and the host moves it'
y0, line_h = layout._CUSTOM_Y[0], 112
assert layout._CUSTOM_ROW_H[0] == layout._CUSTOM_LANG_H == 300, layout._CUSTOM_ROW_H[0]
assert layout._CUSTOM_Y[1] == y0 + 300, layout._CUSTOM_Y[:2]
assert layout._CUSTOM_H == layout._CUSTOM_TITLE_H + sum(layout._CUSTOM_ROW_H), layout._CUSTOM_H
assert nodes['TouchCustomRows']['fields']['rect']['height'] == layout._CUSTOM_H, nodes['TouchCustomRows']['fields']['rect']
below = [n for n, v in nodes.items() if n.startswith('TouchCustom_') and not n.startswith('TouchCustom_lang') and isinstance(v.get('fields', {}).get('rect'), dict)]
assert below and all(nodes[n]['fields']['rect']['y'] >= layout._CUSTOM_Y[1] for n in below), [(n, nodes[n]['fields']['rect']['y']) for n in below if nodes[n]['fields']['rect']['y'] < layout._CUSTOM_Y[1]]
# 每项勾选框在前、字在后（字在勾选框右边 10），五项从左到右不重叠，全在各行勾选框那一列的右沿（1385）以内
# 文字框宽：实宽按俄语界面真包截图量（中文 99、English 166、Español 178、Русский 188；한국어按字体同比约 136），框比实宽多 30 不折行（180 宽时 English 折成「Englis h」）
right = {0: 0, 1: 0}
for key, cap, _, line in opts:
    t = nodes['TouchCustomLang%s_Text' % cap]['fields']['rect']
    b = nodes['TouchCustom_lang_' + key]['fields']['rect']
    assert t['width'] >= {'zh': 129, 'en': 196, 'es': 208, 'ru': 218, 'ko': 166, 'de': 216}[key], (key, t)
    assert b['x'] >= right[line] and t['x'] == b['x'] + 80, (key, b, t)
    assert t['y'] == y0 + line * line_h and t['height'] == line_h and b['y'] == y0 + line * line_h + (line_h - 70) // 2, (key, line, b, t)
    right[line] = t['x'] + t['width']
assert max(right.values()) <= 1385, right
for _, cap, _, _ in opts:
    r = nodes['TouchCustomLangHint%s' % cap]['fields']['rect']
    assert r['y'] == y0 + 2 * line_h and r['y'] + r['height'] <= layout._CUSTOM_Y[1], (cap, r)
# 标签控件还在（宿主拿它定提示与手柄选中框），不写字、横跨整行
lab = nodes['TouchCustom_lang_Text']['fields']
de_box = nodes['TouchCustom_lang_de']['fields']['rect']
assert lab['text'] == '' and lab['rect']['x'] == 0 and lab['rect']['width'] >= max(right.values()), lab
assert lab['rect']['y'] == y0 and lab['rect']['y'] + lab['rect']['height'] >= de_box['y'] + de_box['height'], (lab, de_box)
host = (root / 'host/dm_custom.c').read_text()
boxes = re.findall(r'"(TouchCustom_lang_[a-z]+)"', re.search(r'k_lang_box\[LANG_N\].*?=\s*\{(.*?)\}', host, re.S)[1])
assert boxes == ['TouchCustom_lang_' + k for k, _, _, _ in opts], boxes
assert re.search(r'#define LANG_N 6\b', host), 'LANG_N must be 6'
rightmost = max((o for o in opts if o[3] == 0), key=lambda o: nodes['TouchCustom_lang_' + o[0]]['fields']['rect']['x'])
assert re.search(r'#define LANG_RIGHT %d\b' % opts.index(rightmost), host), 'LANG_RIGHT must be the index of TouchCustom_lang_%s' % rightmost[0]
print('PASS touch layout language row: six-option radio on two lines, labels, hints, row height, checkbox column and host order')
