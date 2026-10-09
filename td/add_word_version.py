r"""One-object 3D word version (live show snapshot).

Does not destroy the per-letter sim.

In the Textport:
  exec(open(r"C:\path\to\td\add_word_version.py", encoding="utf-8").read())

Back to letters:
  op('/project1/virtual_room/screen_3d/text_mode').par.value0 = 0
  op('/project1/virtual_room/screen_3d/set_mode').run()
"""

S3 = '/project1/virtual_room/screen_3d'
BASE = '/project1/virtual_room'

IMPULSE = 8.5
SPAWN_Y = 2.3
GRAVITY = -6.5
SPIN = 30
SPIN_Y = 20
WORD_SZ = 0.06
SHOW_SEC = 3.0
BLACK_SEC = 3.0
CAM_TY = 9.3
GROUND_SIZE = 40
PLATE_EMIT = 0.72
FLOOR_HI = 7.5
FLOOR_LO = 0.2
FLOOR_EMIT = 0.28
LIGHT_DIM = 0.55


def par(node, name):
    try:
        return node.par[name]
    except Exception:
        return None


def setp(node, names, value):
    if node is None:
        return False
    for n in names:
        p = par(node, n)
        if p is None:
            continue
        try:
            p.expr = ''
        except Exception:
            pass
        try:
            p.val = value
            return True
        except Exception:
            continue
    return False


def flags(n, display, render):
    if n is None:
        return
    try:
        n.display = display
        n.render = render
    except Exception:
        pass
    try:
        n.current = render
    except Exception:
        pass


def hook(dst, idx, src):
    if dst is None or src is None:
        return
    try:
        con = dst.inputConnectors[idx]
        if con.connections:
            con.disconnect()
        con.connect(src)
    except Exception as e:
        print('word_version: hook', dst, e)


s3 = op(S3)
b = op(BASE)
if s3 is None or b is None:
    raise RuntimeError('missing virtual_room / screen_3d')

mode = s3.op('text_mode')
if mode is None:
    mode = s3.create(constantCHOP, 'text_mode')
    mode.nodeX, mode.nodeY = 0, -600
mode.par.name0 = 'mode'
mode.par.value0 = 1

wg = s3.op('word_geo')
if wg is None:
    wg = s3.create(geometryCOMP, 'word_geo')
wg.nodeX, wg.nodeY = 200, 600
for c in list(wg.children):
    c.destroy()
ts = wg.create(textSOP, 'text1')
ext = wg.create(extrudeSOP, 'extrude1')
try:
    ext.inputConnectors[0].connect(ts)
except Exception:
    try:
        ts.outputConnectors[0].connect(ext.inputConnectors[0])
    except Exception as e:
        print('word_version: extrude wire', e)
flags(ts, False, False)
flags(ext, True, True)

l0 = s3.op('letters/L0/text1')
font = 'Microsoft JhengHei'
if l0 is not None:
    p = par(l0, 'font')
    if p is not None:
        try:
            font = p.eval()
        except Exception:
            font = p.val
setp(ts, ['font'], font)
setp(ts, ['fontsize', 'fontsizex', 'fontsizey'], 0.22)
setp(ts, ['align'], 'center')
setp(ts, ['alignx'], 'center')
setp(ts, ['aligny'], 'center')
setp(ext, ['depth'], 0.08)
setp(ts, ['text'], 'TEST')
tm = s3.op('text_lit') or s3.op('text_mat')
if tm is not None:
    wg.par.material = tm.path
    setp(tm, ['emitr', 'emitg', 'emitb'], 1)
    setp(tm, ['diffr', 'diffg', 'diffb'], 0)
    setp(tm, ['twosided', 'doubleface'], True)
wg.par.sx, wg.par.sy, wg.par.sz = 1, -1, WORD_SZ
wg.par.rx, wg.par.ry, wg.par.rz = 90, 0, 0
wg.par.tx, wg.par.ty, wg.par.tz = 0, SPAWN_Y, 0
wg.render = True
wg.display = True
setp(wg, ['cullface', 'cull'], 'off')

wl = s3.op('word_light')
if wl is None:
    wl = s3.create(lightCOMP, 'word_light')
wl.nodeX, wl.nodeY = 400, 700
setp(wl, ['lighttype'], 'point')
setp(wl, ['colorr'], 1)
setp(wl, ['colorg'], 1)
setp(wl, ['colorb'], 1)
setp(wl, ['dimmer'], 2)
setp(wl, ['attenuate', 'atten'], False)
wl.par.tx, wl.par.ty, wl.par.tz = 0, SPAWN_Y + 0.08, 0

vb = s3.op('vol_bright')
if vb is None:
    vb = s3.create(constantCHOP, 'vol_bright')
    vb.nodeX, vb.nodeY = 200, -600
vb.par.name0 = 'b'
vb.par.value0 = 1

ws = s3.op('word_state')
if ws is None:
    ws = s3.create(tableDAT, 'word_state')
ws.nodeX, ws.nodeY = 400, 500

cam = s3.op('cam_top')
if cam is not None:
    cam.par.ty = CAM_TY
    cam.par.rx = -90

gg = s3.op('ground_geo')
if gg is None:
    gg = s3.create(geometryCOMP, 'ground_geo')
    gg.nodeX, gg.nodeY = 200, 400
box = gg.op('box1') if gg else None
if box is None and gg is not None:
    for c in list(gg.children):
        c.destroy()
    box = gg.create(boxSOP, 'box1')
if box is not None:
    box.par.sizex = GROUND_SIZE
    box.par.sizey = 0.03
    box.par.sizez = GROUND_SIZE
    flags(box, True, True)
gg.par.tx, gg.par.ty, gg.par.tz = 0, -0.16, 0
gg.par.rx, gg.par.ry, gg.par.rz = 0, 0, 0
gg.render = True
gg.display = True

rr = s3.op('word_reflect')
if rr is None:
    rr = s3.create(renderTOP, 'word_reflect')
    rr.nodeX, rr.nodeY = 200, 200
rr.par.camera = 'cam_top'
rr.par.geometry = wg.path
key = s3.op('key')
rr.par.lights = ((key.path + ' ') if key else '') + (wl.path if wl else '')
setp(rr, ['bgcolorr', 'bgcolorg', 'bgcolorb'], 0)
flp = s3.op('word_reflect_flip')
if flp is None:
    flp = s3.create(flipTOP, 'word_reflect_flip')
    flp.nodeX, flp.nodeY = 400, 200
setp(flp, ['flipy', 'flipr'], True)
hook(flp, 0, rr)
rblur = s3.op('word_reflect_blur')
if rblur is None:
    rblur = s3.create(blurTOP, 'word_reflect_blur')
    rblur.nodeX, rblur.nodeY = 600, 200
setp(rblur, ['filtersize', 'size', 'kernelsize', 'blursize'], 16)
hook(rblur, 0, flp)
rlev = s3.op('word_reflect_level')
if rlev is None:
    rlev = s3.create(levelTOP, 'word_reflect_level')
    rlev.nodeX, rlev.nodeY = 800, 200
setp(rlev, ['brightness1', 'brightness', 'gain1'], 0.85)
hook(rlev, 0, rblur)

gm = s3.op('ground_reflect_mat')
if gm is None:
    gm = s3.create(phongMAT, 'ground_reflect_mat')
    gm.nodeX, gm.nodeY = 800, 400
setp(gm, ['ambr', 'ambg', 'ambb'], 0)
setp(gm, ['diffr'], 0.045)
setp(gm, ['diffg'], 0.045)
setp(gm, ['diffb'], 0.045)
setp(gm, ['emitr'], 1)
setp(gm, ['emitg'], 0.96)
setp(gm, ['emitb'], 0.88)
setp(gm, ['specr', 'specg', 'specb'], 0)
for n in ('emitmap', 'emissionmap'):
    if setp(gm, [n], rlev.path):
        break
gg.par.material = gm.path

rnd = s3.op('text3d_render')
if rnd is not None:
    rnd.par.geometry = '*'
    rnd.par.camera = 'cam_top'

launch = s3.op('word_launch')
if launch is None:
    launch = s3.create(textDAT, 'word_launch')
launch.nodeX, launch.nodeY = 800, 500
launch.text = r'''import math
import random
s3 = op("/project1/virtual_room/screen_3d")
b = op("/project1/virtual_room")
st = s3.op("word_state")
wg = s3.op("word_geo")
seq = s3.op("seq")
vb = s3.op("vol_bright")
tm = s3.op("text_lit")
IMPULSE = 8.5
SPAWN_Y = 2.3

def parse_vol(v):
    s = str(v).strip().upper().replace(",", "").replace("+", "").replace(" ", "")
    if not s:
        return 0.0
    mul = 1.0
    if s.endswith("K"):
        mul = 1000.0
        s = s[:-1]
    elif s.endswith("M"):
        mul = 1000000.0
        s = s[:-1]
    try:
        return float(s) * mul
    except:
        return 0.0

table = b.op("trends_table")
idx = b.op("trend_index")
word = "TRENDING"
vol = 0.0
if table is not None and table.numRows > 1:
    i = int(idx.par.value0) % max(1, table.numRows - 1)
    row = i + 1
    word = str(table[row, 0]).replace(" ", "") or "?"
    try:
        vol = parse_vol(table[row, "search_volume"])
    except:
        vol = parse_vol(table[row, 1])
    vols = []
    for r in range(1, table.numRows):
        try:
            vols.append(parse_vol(table[r, "search_volume"]))
        except:
            vols.append(parse_vol(table[r, 1]))
    lo = min(vols) if vols else 0.0
    hi = max(vols) if vols else 0.0
    if hi > lo:
        t = (math.log10(max(vol, 1.0)) - math.log10(max(lo, 1.0))) / (math.log10(max(hi, 1.0)) - math.log10(max(lo, 1.0)))
    else:
        t = 0.5
    t = max(0.0, min(1.0, t))
else:
    t = 0.5
bright = 0.75 + 0.25 * t
if vb is not None:
    vb.par.value0 = bright
if tm is not None:
    try:
        tm.par.emitr = tm.par.emitg = tm.par.emitb = bright
    except:
        pass
ts = wg.op("text1") if wg else None
ext = wg.op("extrude1") if wg else None
if ts is not None:
    ts.par.text = word
    ts.display = False
    ts.render = False
if ext is not None:
    ext.display = True
    ext.render = True
wx = random.uniform(-30, 30)
wy = random.uniform(-20, 20)
wz = random.uniform(-30, 30)
st.clear()
st.appendRow(["on", "x", "y", "z", "vx", "vy", "vz", "rx", "ry", "rz", "wx", "wy", "wz"])
st.appendRow([1, 0, SPAWN_Y, 0, 0, IMPULSE, 0, 90, 0, 0, wx, wy, wz])
if wg is not None:
    wg.par.sx, wg.par.sy, wg.par.sz = 1, -1, 0.06
    wg.par.tx, wg.par.ty, wg.par.tz = 0, SPAWN_Y, 0
    wg.par.rx, wg.par.ry, wg.par.rz = 90, 0, 0
    if tm is not None:
        wg.par.material = tm.path
    wg.render = True
    wg.display = True
if seq is not None:
    seq.par.value0 = 0
    seq.par.value1 = 0
    seq.par.value2 = 0
print("word launch", word, "vol", vol, "bright", round(bright, 3))
'''

tick = s3.op('word_tick')
if tick is None:
    tick = s3.create(executeDAT, 'word_tick')
tick.nodeX, tick.nodeY = 800, 300
tick.par.frameend = True
tick.text = r'''def onStart():
    return
def onCreate():
    return
def onExit():
    return
def onFrameStart(frame):
    return
def onPlayStateChange(state):
    return
def onDeviceChange():
    return
def onProjectPreSave():
    return
def onProjectPostSave():
    return
def onFrameEnd(frame):
    s3 = op("/project1/virtual_room/screen_3d")
    mode = s3.op("text_mode")
    if mode is None or int(float(mode.par.value0)) != 1:
        return
    st = s3.op("word_state")
    wg = s3.op("word_geo")
    seq = s3.op("seq")
    wl = s3.op("word_light")
    vb = s3.op("vol_bright")
    b = op("/project1/virtual_room")
    if st is None or wg is None or st.numRows < 2:
        return
    dt = 1.0 / 60.0
    try:
        dt = float(absTime.step)
        if dt <= 0 or dt > 0.05:
            dt = 1.0 / 60.0
    except:
        pass
    phase = int(float(seq.par.value0)) if seq else 0
    t = float(seq.par.value1) if seq else 0
    G = -6.5
    REST = 0.38
    WALL = 2.4
    SHOW = 3.0
    BLACK_HOLD = 3.0
    on = int(float(st[1, 0]))
    x = float(st[1, 1])
    y = float(st[1, 2])
    z = float(st[1, 3])
    vx = float(st[1, 4])
    vy = float(st[1, 5])
    vz = float(st[1, 6])
    rx = float(st[1, 7]) if st.numCols > 7 else 90.0
    ry = float(st[1, 8]) if st.numCols > 8 else 0.0
    rz = float(st[1, 9]) if st.numCols > 9 else 0.0
    wx = float(st[1, 10]) if st.numCols > 10 else 0.0
    wy = float(st[1, 11]) if st.numCols > 11 else 0.0
    wz = float(st[1, 12]) if st.numCols > 12 else 0.0
    if phase == 1 or phase == 2:
        phase = 0
    if phase == 0:
        vy += G * dt
        x += vx * dt
        y += vy * dt
        z += vz * dt
        rx += wx * dt
        ry += wy * dt
        rz += wz * dt
        if x < -WALL:
            x, vx = -WALL, abs(vx) * REST
        elif x > WALL:
            x, vx = WALL, -abs(vx) * REST
        if z < -1.5:
            z, vz = -1.5, abs(vz) * REST
        elif z > 1.5:
            z, vz = 1.5, -abs(vz) * REST
        t += dt
        on = 1
        if t >= SHOW:
            on = 0
            phase, t = 3, 0
    elif phase == 3:
        t += dt
        on = 0
        if t >= BLACK_HOLD:
            table = b.op("trends_table")
            idx = b.op("trend_index")
            nn = max(1, table.numRows - 1)
            idx.par.value0 = (int(idx.par.value0) + 1) % nn
            if seq is not None:
                seq.par.value0 = 0
                seq.par.value1 = 0
                seq.par.value2 = 0
            s3.op("word_launch").run()
            return
    if seq is not None:
        seq.par.value0 = phase
        seq.par.value1 = t
    st[1, 0] = on
    st[1, 1], st[1, 2], st[1, 3] = x, y, z
    st[1, 4], st[1, 5], st[1, 6] = vx, vy, vz
    try:
        st[1, 7], st[1, 8], st[1, 9] = rx, ry, rz
        st[1, 10], st[1, 11], st[1, 12] = wx, wy, wz
    except:
        pass
    wg.par.sx, wg.par.sy, wg.par.sz = 1, -1, 0.06
    wg.par.rx, wg.par.ry, wg.par.rz = rx, ry, rz
    ext = wg.op("extrude1")
    if ext is not None:
        ext.display = True
        ext.render = True
    show = on == 1
    if show:
        wg.par.tx, wg.par.ty, wg.par.tz = x, y, z
        wg.render = True
        wg.display = True
    else:
        wg.render = False
        wg.display = False
    if wl is not None:
        bright = 1.0
        if vb is not None:
            try:
                bright = float(vb.par.value0)
            except:
                pass
        wl.par.tx = x
        wl.par.ty = y + 0.08
        wl.par.tz = z
        wl.par.dimmer = (4.0 * bright) if show else 0
    return
'''

sm = s3.op('set_mode')
if sm is None:
    sm = s3.create(textDAT, 'set_mode')
sm.nodeX, sm.nodeY = 0, -700
sm.text = r'''s3 = op("/project1/virtual_room/screen_3d")
mode = int(float(s3.op("text_mode").par.value0))
rnd = s3.op("text3d_render")
holder = s3.op("letters")
wg = s3.op("word_geo")
wl = s3.op("word_light")
gg = s3.op("ground_geo")
pt = s3.op("phys_tick")
gt = s3.op("glow_tick")
wt = s3.op("word_tick")
key = s3.op("key")
word = (mode == 1)

if pt is not None:
    pt.par.frameend = not word
if gt is not None:
    gt.par.frameend = not word
if wt is not None:
    wt.par.frameend = word

if holder is not None:
    for c in holder.children:
        c.render = False if word else c.render
        c.display = False if word else c.display
if not word and holder is not None:
    s3.op("run_launch").run()
if wg is not None:
    wg.render = word
    wg.display = word
    ext = wg.op("extrude1")
    if ext is not None and word:
        ext.display = True
        ext.render = True

for i in range(16):
    lg = s3.op("glow%d" % i)
    if lg is not None and word:
        lg.par.dimmer = 0
if wl is not None and not word:
    wl.par.dimmer = 0
if gg is not None:
    gg.render = True
    gg.display = True
    if word:
        rm = s3.op("ground_reflect_mat")
        if rm is not None:
            gg.par.material = rm.path

if rnd is not None:
    rnd.par.camera = "cam_top"
    if word:
        rnd.par.geometry = "*"
        lights = []
        if key is not None:
            lights.append(key.path)
        if wl is not None:
            lights.append(wl.path)
        rnd.par.lights = " ".join(lights)
    else:
        rnd.par.geometry = "/project1/virtual_room/screen_3d/letters/* /project1/virtual_room/screen_3d/ground_geo"
        lights = []
        if key is not None:
            lights.append(key.path)
        for i in range(16):
            lg = s3.op("glow%d" % i)
            if lg is not None:
                lights.append(lg.path)
        rnd.par.lights = " ".join(lights) if lights else "*"

if word:
    s3.op("word_launch").run()
print("text_mode", mode, "word" if word else "letters")
'''

# --- virtual_room plate + floor wash (word rises => floor lights up)
src = s3.op('letter_halo') or s3.op('text3d_render')
em = b.op('screen_emit_mat')
if em is None:
    em = b.create(phongMAT, 'screen_emit_mat')
    em.nodeX, em.nodeY = 600, 400
setp(em, ['ambr', 'ambg', 'ambb'], 0)
setp(em, ['diffr', 'diffg', 'diffb'], 0)
setp(em, ['specr', 'specg', 'specb'], 0)
setp(em, ['emitr'], PLATE_EMIT)
setp(em, ['emitg'], PLATE_EMIT)
setp(em, ['emitb'], PLATE_EMIT)
if src is not None:
    for n in ('emitmap', 'emissionmap', 'colormap'):
        setp(em, [n], src.path)
sm_mat = b.op('screen_mat')
if sm_mat is not None:
    setp(sm_mat, ['colorr'], 1)
    setp(sm_mat, ['colorg'], 1)
    setp(sm_mat, ['colorb'], 1)
    if src is not None:
        setp(sm_mat, ['colormap'], src.path)
        setp(sm_mat, ['usecolormap', 'applycolormap', 'colormapon'], True)
sg = b.op('screen_geo')
if sg is not None:
    sg.par.material = em.path
    sg.render = True
    sg.display = True
    setp(sg, ['cullface', 'cull'], 'off')

fp = b.op('floor_phong')
if fp is None:
    fp = b.create(phongMAT, 'floor_phong')
    fp.nodeX, fp.nodeY = 400, 350
setp(fp, ['ambr', 'ambg', 'ambb'], 0)
setp(fp, ['diffr', 'diffg', 'diffb'], 0.07)
setp(fp, ['specr', 'specg', 'specb'], 0)
setp(fp, ['emitr', 'emitg', 'emitb'], 0)
fl = b.op('floor')
if fl is not None:
    fl.par.material = fp.path

ch = b.op('floor_glow')
if ch is None:
    ch = b.create(constantCHOP, 'floor_glow')
    ch.nodeX, ch.nodeY = 800, -200
ch.par.name0 = 'g'
ch.par.value0 = 0

L = b.op('screen_light')
if L is not None:
    try:
        L.par.dimmer.expr = ''
    except Exception:
        pass
    L.par.tx, L.par.ty, L.par.tz = 0, 0.22, 0
    setp(L, ['dimmer', 'intensity'], 0)

glow_tick = b.op('floor_glow_tick')
if glow_tick is None:
    glow_tick = b.create(executeDAT, 'floor_glow_tick')
    glow_tick.nodeX, glow_tick.nodeY = 1000, -200
glow_tick.par.frameend = True
glow_tick.text = r'''def onStart():
    return
def onCreate():
    return
def onExit():
    return
def onFrameStart(frame):
    return
def onPlayStateChange(state):
    return
def onDeviceChange():
    return
def onProjectPreSave():
    return
def onProjectPostSave():
    return
def onFrameEnd(frame):
    b = op("/project1/virtual_room")
    s3 = b.op("screen_3d")
    ch = b.op("floor_glow")
    fp = b.op("floor_phong")
    L = b.op("screen_light")
    if ch is None:
        return
    dt = 1.0 / 60.0
    try:
        dt = float(absTime.step)
        if dt <= 0 or dt > 0.05:
            dt = 1.0 / 60.0
    except:
        pass
    show = False
    y = 0.0
    phase = 0
    if s3 is not None:
        wg = s3.op("word_geo")
        seq = s3.op("seq")
        if wg is not None:
            try:
                show = bool(wg.render) and bool(wg.display)
            except:
                show = False
            try:
                y = float(wg.par.ty)
            except:
                pass
        if seq is not None:
            try:
                phase = int(float(seq.par.value0))
            except:
                pass
    if (not show) or phase >= 3 or y < -0.2:
        target = 0.0
    else:
        lo = 0.2
        hi = 7.5
        if y <= lo:
            target = 0.0
        elif y >= hi:
            target = 1.0
        else:
            target = (y - lo) / (hi - lo)
    cur = float(ch.par.value0)
    cur = cur + (target - cur) * min(1.0, 3.2 * dt)
    ch.par.value0 = cur
    if fp is not None:
        e = cur * 0.28
        try:
            fp.par.emitr = e
            fp.par.emitg = e * 0.96
            fp.par.emitb = e * 0.88
        except:
            pass
    if L is not None:
        try:
            L.par.dimmer = cur * 0.55
        except:
            pass
    return
'''

sm.run()
print('word_version: one thin tumbling word, 3s on / 3s black, floor lights as it rises')
print('letters again: text_mode=0 then set_mode.run()')
