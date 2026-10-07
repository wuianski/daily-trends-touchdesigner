r"""Add a second inner-scene version: the whole trend as ONE 3D object.

Does NOT destroy the per-letter version.

In the Textport:
  exec(open(r"C:\path\to\td\add_word_version.py", encoding="utf-8").read())

Switch:
  op('/project1/virtual_room/screen_3d/text_mode').par.value0 = 1  # this version
  op('/project1/virtual_room/screen_3d/set_mode').run()
  op('/project1/virtual_room/screen_3d/text_mode').par.value0 = 0  # letters
  op('/project1/virtual_room/screen_3d/set_mode').run()
"""

S3 = '/project1/virtual_room/screen_3d'
BASE = '/project1/virtual_room'


def par(node, name):
    try:
        return node.par[name]
    except Exception:
        try:
            return getattr(node.par, name)
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
            try:
                setattr(node.par, n, value)
                return True
            except Exception:
                continue
    return False


def hook(dst, idx, src):
    if dst is None or src is None:
        print('word_version: hook skip', dst, src)
        return
    try:
        con = dst.inputConnectors[idx]
        if con.connections:
            con.disconnect()
        con.connect(src)
        print('word_version: hooked', dst.name, idx, src.name)
    except Exception as e:
        print('word_version: hook fail', dst.name, idx, e)


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

# --- one mesh for the whole word ---
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
    pass

l0 = s3.op('letters/L0/text1')
font = 'Microsoft JhengHei'
size = 0.16
depth = 0.08
if l0 is not None:
    p = par(l0, 'font')
    if p is not None:
        font = str(p)
    p = par(l0, 'fontsize')
    if p is None:
        p = par(l0, 'fontsizex')
    if p is not None:
        try:
            size = float(p)
        except Exception:
            pass
l0e = s3.op('letters/L0/extrude1')
if l0e is not None:
    p = par(l0e, 'depth')
    if p is not None:
        try:
            depth = float(p)
        except Exception:
            pass
setp(ts, ['font'], font)
setp(ts, ['fontsize', 'fontsizex'], size)
setp(ts, ['align'], 'center')
setp(ts, ['alignx'], 'center')
setp(ts, ['aligny'], 'center')
setp(ext, ['depth'], depth)
tm = s3.op('text_lit') or s3.op('text_mat')
if tm is not None:
    wg.par.material = tm.path
wg.par.rx, wg.par.ry, wg.par.rz = -90, 0, 0
setp(wg, ['cullface', 'cull'], 'off')

# --- one lamp that rides with the word ---
wl = s3.op('word_light')
if wl is None:
    wl = s3.create(lightCOMP, 'word_light')
wl.nodeX, wl.nodeY = 400, 700
setp(wl, ['lighttype'], 'point')
setp(wl, ['colorr'], 1)
setp(wl, ['colorg'], 1)
setp(wl, ['colorb'], 1)
setp(wl, ['dimmer'], 0)
setp(wl, ['attenuate', 'atten'], True)
setp(wl, ['attenconst', 'attenconstant'], 1)
setp(wl, ['attenlin', 'attenlinear'], 0.6)
setp(wl, ['attenquad', 'attenquadratic'], 2.5)

ws = s3.op('word_state')
if ws is None:
    ws = s3.create(tableDAT, 'word_state')
ws.nodeX, ws.nodeY = 400, 500

# --- floor reflection of the glowing word ---
cam_t = s3.op('cam_top')
cr = s3.op('cam_reflect')
if cr is None:
    cr = s3.create(cameraCOMP, 'cam_reflect')
cr.nodeX, cr.nodeY = 0, 200
cr.par.tx = 0
cr.par.tz = 0
try:
    cr.par.ty = -float(cam_t.par.ty) if cam_t else -4.5
except Exception:
    cr.par.ty = -4.5
cr.par.rx = 90
cr.par.ry = 0
cr.par.rz = 180
if cam_t is not None:
    setp(cr, ['fov', 'fovx'], float(par(cam_t, 'fov') or par(cam_t, 'fovx') or 75))

rr = s3.op('word_reflect')
if rr is None:
    rr = s3.create(renderTOP, 'word_reflect')
rr.nodeX, rr.nodeY = 200, 200
rr.par.camera = cr.path
rr.par.geometry = wg.path
rr.par.lights = ' '.join([p for p in (
    s3.op('key').path if s3.op('key') else '',
    wl.path,
) if p])
setp(rr, ['bgcolorr'], 0)
setp(rr, ['bgcolorg'], 0)
setp(rr, ['bgcolorb'], 0)
setp(rr, ['bgalpha'], 1)
try:
    rr.par.resolutionw = 1024
    rr.par.resolutionh = 1024
except Exception:
    pass

rblur = s3.op('word_reflect_blur')
if rblur is None:
    rblur = s3.create(blurTOP, 'word_reflect_blur')
rblur.nodeX, rblur.nodeY = 400, 200
setp(rblur, ['filtersize', 'size', 'kernelsize', 'blursize'], 10)
hook(rblur, 0, rr)

rlev = s3.op('word_reflect_level')
if rlev is None:
    rlev = s3.create(levelTOP, 'word_reflect_level')
rlev.nodeX, rlev.nodeY = 600, 200
setp(rlev, ['brightness1', 'brightness', 'gain1'], 0.45)
hook(rlev, 0, rblur)

gm = s3.op('ground_reflect_mat')
if gm is None:
    gm = s3.create(phongMAT, 'ground_reflect_mat')
gm.nodeX, gm.nodeY = 800, 400
setp(gm, ['ambr', 'ambientr'], 0)
setp(gm, ['ambg', 'ambientg'], 0)
setp(gm, ['ambb', 'ambientb'], 0)
setp(gm, ['diffr', 'diffuser'], 0.06)
setp(gm, ['diffg', 'diffuseg'], 0.06)
setp(gm, ['diffb', 'diffuseb'], 0.06)
setp(gm, ['emitr', 'emissionr'], 0.7)
setp(gm, ['emitg', 'emissiong'], 0.7)
setp(gm, ['emitb', 'emissionb'], 0.7)
setp(gm, ['specr'], 0.25)
setp(gm, ['specg'], 0.25)
setp(gm, ['specb'], 0.25)
setp(gm, ['roughness'], 0.35)
setp(gm, ['shininess'], 12)
setp(gm, ['twosided', 'doubleface'], True)
for n in ('emitmap', 'emissionmap', 'colormap'):
    setp(gm, [n], rlev.path)
setp(gm, ['useemitmap', 'useemissionmap', 'usecolormap'], True)

# --- launch the whole word ---
launch = s3.op('word_launch')
if launch is None:
    launch = s3.create(textDAT, 'word_launch')
launch.nodeX, launch.nodeY = 800, 500
launch.text = r'''import math
s3 = op("/project1/virtual_room/screen_3d")
b = op("/project1/virtual_room")
st = s3.op("word_state")
wg = s3.op("word_geo")
seq = s3.op("seq")
vb = s3.op("vol_bright")
tm = s3.op("text_lit")
IMPULSE = 8.0

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
bright = 0.18 + 0.32 * t
if vb is not None:
    vb.par.value0 = bright
if tm is not None:
    try:
        tm.par.emitr = tm.par.emitg = tm.par.emitb = bright
    except:
        pass
ts = wg.op("text1") if wg else None
if ts is not None:
    ts.par.text = word
st.clear()
st.appendRow(["on", "x", "y", "z", "vx", "vy", "vz"])
st.appendRow([1, 0, 0.55, 0, 0, IMPULSE, 0])
if wg is not None:
    wg.par.tx, wg.par.ty, wg.par.tz = 0, 0.55, 0
    wg.par.rx, wg.par.ry, wg.par.rz = -90, 0, 0
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

# --- single-body physics (same phases as letters: fly, sink through, black) ---
tick = s3.op('word_tick')
if tick is None:
    tick = s3.create(executeDAT, 'word_tick')
tick.nodeX, tick.nodeY = 800, 300
tick.par.frameend = False
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
    G = -14.0
    REST = 0.55
    FLOOR = 0.22
    WALL = 2.4
    SINK_SPEED = 1.4
    BLACK_HOLD = 2.2
    HIDE = -1.1
    on = int(float(st[1, "on"]))
    x = float(st[1, "x"])
    y = float(st[1, "y"])
    z = float(st[1, "z"])
    vx = float(st[1, "vx"])
    vy = float(st[1, "vy"])
    vz = float(st[1, "vz"])

    if phase == 0:
        vy += G * dt
        x += vx * dt
        y += vy * dt
        z += vz * dt
        if x < -WALL:
            x, vx = -WALL, abs(vx) * REST
        elif x > WALL:
            x, vx = WALL, -abs(vx) * REST
        if z < -1.5:
            z, vz = -1.5, abs(vz) * REST
        elif z > 1.5:
            z, vz = 1.5, -abs(vz) * REST
        t += dt
        if y < HIDE:
            on = 0
            phase, t = 3, 0
        elif y < FLOOR:
            phase, t = 2, 0
    elif phase == 1:
        phase, t = 2, 0
    elif phase == 2:
        t += dt
        y -= SINK_SPEED * dt
        vx = vy = vz = 0
        if y < HIDE:
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
    st[1, "on"] = on
    st[1, "x"], st[1, "y"], st[1, "z"] = x, y, z
    st[1, "vx"], st[1, "vy"], st[1, "vz"] = vx, vy, vz
    wg.par.rx, wg.par.ry, wg.par.rz = -90, 0, 0
    show = on and y > HIDE
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
        wl.par.dimmer = (3.0 * bright) if show else 0
    return
'''

# --- switch between letter version and word version ---
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
        c.render = (not word)
        c.display = (not word)
        if word:
            c.render = False
            c.display = False
if wg is not None:
    wg.render = word
    wg.display = word

for i in range(16):
    lg = s3.op("glow%d" % i)
    if lg is not None and word:
        lg.par.dimmer = 0

if wl is not None and not word:
    wl.par.dimmer = 0

if gg is not None:
    if word:
        rm = s3.op("ground_reflect_mat")
        if rm is not None:
            gg.par.material = rm.path
    else:
        gl = s3.op("ground_lit") or s3.op("ground_mat")
        if gl is not None:
            gg.par.material = gl.path
    gg.render = True

if rnd is not None:
    if word:
        rnd.par.geometry = "word_geo ground_geo"
        lights = []
        if key is not None:
            lights.append(key.path)
        if wl is not None:
            lights.append(wl.path)
        rnd.par.lights = " ".join(lights)
        rr = s3.op("word_reflect")
        if rr is not None:
            rr.par.geometry = "word_geo"
            rr.par.lights = rnd.par.lights
    else:
        rnd.par.geometry = "letters/* ground_geo"
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
else:
    s3.op("run_launch").run()
print("text_mode", mode, "word" if word else "letters")
'''

sm.run()
print('word_version: ready. text_mode=1 (one object). letters version is kept at text_mode=0')
