r"""Builder for "The screen going on and off" virtual room network.

Run this ONCE inside TouchDesigner to create the whole network
programmatically (TouchDesigner project files are binary, so the network
is built by script instead of shipped as a .toe).

How to run:
  1. Open TouchDesigner (default project with /project1).
  2. Open the Textport (Alt+T, or Dialogs > Textport and DATs).
  3. Type (adjust the path):
       exec(open(r"C:\path\to\td\build_virtual_room.py", encoding="utf-8").read())

What it creates: /project1/virtual_room containing
  - room_mat + 5 wall slabs (floor / ceiling / back / left / right,
    front side left open for the camera) forming a dark room
  - screen_geo: a 16:9 rectangle lying on the floor (the virtual screen)
  - trends_table: table with columns query/search_volume/categories/
    trend_breakdown (same format the trends_loader script fills)
  - screen_text: Text TOP showing ONE trend query at a time
  - pulse: square-wave LFO CHOP = the on/off rhythm of the inner screen
  - screen_level: Level TOP gating the text by the pulse (screen dark when off)
  - screen_light: point light above the screen, dimmer follows the pulse,
    so the whole virtual room brightens and darkens with the screen
  - trend_cycler: CHOP Execute DAT that advances to the next trend each
    time the screen turns on
  - cam1 + render1 + OUT (1920x1080) - fullscreen this on the real screen

Safe to re-run: the previous virtual_room is destroyed and rebuilt.
After building, run td/trends_loader.py (pointed at data/latest.json and
targeting /project1/virtual_room/trends_table) to load the real daily trends.
"""

PROJECT_PATH = '/project1'
COMP_NAME = 'virtual_room'

# Room dimensions in meters (adjust to match the real exhibition space)
ROOM_W, ROOM_H, ROOM_D = 6.0, 3.0, 6.0
WALL_T = 0.1
SCREEN_W, SCREEN_H = 1.6, 0.9      # floor screen, 16:9
PULSE_PERIOD = 8.0                 # seconds for one full on/off cycle


def get_par(node, name):
    """Look up a parameter. TD's ParCollection raises tdAttributeError
    (not AttributeError) when a name is missing, so getattr(..., None)
    is not safe."""
    try:
        return node.par[name]
    except Exception:
        try:
            return getattr(node.par, name)
        except Exception:
            return None


def set_first_par(node, names, value):
    """Set the first existing parameter from names (handles TD version
    differences, e.g. Text TOP fontsizex vs fontsize, LFO amp vs amplitude)."""
    for n in names:
        p = get_par(node, n)
        if p is None:
            continue
        try:
            p.val = value
            return True
        except Exception:
            pass
        try:
            setattr(node.par, n, value)
            return True
        except Exception:
            continue
    print('build_virtual_room: none of pars {} on {}'.format(names, node.path))
    return False


def set_first_par_expr(node, names, expr):
    for n in names:
        p = get_par(node, n)
        if p is None:
            continue
        try:
            p.expr = expr
            return True
        except Exception:
            continue
    print('build_virtual_room: none of expr pars {} on {}'.format(names, node.path))
    return False


proj = op(PROJECT_PATH)
if proj is None:
    raise RuntimeError('Project path not found: {}'.format(PROJECT_PATH))

old = proj.op(COMP_NAME)
if old is not None:
    old.destroy()

base = proj.create(baseCOMP, COMP_NAME)

# ---------------------------------------------------------------- materials
room_mat = base.create(phongMAT, 'room_mat')
room_mat.nodeX, room_mat.nodeY = 0, 400
# No ambient / emission: walls are invisible until the screen light hits them.
set_first_par(room_mat, ['ambr', 'ambientr'], 0)
set_first_par(room_mat, ['ambg', 'ambientg'], 0)
set_first_par(room_mat, ['ambb', 'ambientb'], 0)
set_first_par(room_mat, ['emitr', 'emissionr'], 0)
set_first_par(room_mat, ['emitg', 'emissiong'], 0)
set_first_par(room_mat, ['emitb', 'emissionb'], 0)
set_first_par(room_mat, ['specr', 'specularr'], 0)
set_first_par(room_mat, ['specg', 'specularg'], 0)
set_first_par(room_mat, ['specb', 'specularb'], 0)
ONOFF = "1 if op('pulse')[0] > 0.5 else 0"
set_first_par_expr(room_mat, ['diffr', 'diffuser'], ONOFF + '*0.12')
set_first_par_expr(room_mat, ['diffg', 'diffuseg'], ONOFF + '*0.12')
set_first_par_expr(room_mat, ['diffb', 'diffuseb'], ONOFF + '*0.12')

screen_mat = base.create(constantMAT, 'screen_mat')
screen_mat.nodeX, screen_mat.nodeY = 200, 400
screen_mat.par.colormap = 'screen_level'

# -------------------------------------------------------------------- room


def make_wall(name, size, pos, node_x, node_y):
    geo = base.create(geometryCOMP, name)
    geo.nodeX, geo.nodeY = node_x, node_y
    for child in geo.children:      # remove any default SOP
        child.destroy()
    box = geo.create(boxSOP, 'box1')
    box.par.sizex, box.par.sizey, box.par.sizez = size
    box.display = True
    box.render = True
    geo.par.tx, geo.par.ty, geo.par.tz = pos
    geo.par.material = '../room_mat'
    return geo


walls = [
    ('floor',      (ROOM_W, WALL_T, ROOM_D), (0, -WALL_T / 2, 0)),
    ('ceiling',    (ROOM_W, WALL_T, ROOM_D), (0, ROOM_H + WALL_T / 2, 0)),
    ('wall_back',  (ROOM_W, ROOM_H, WALL_T), (0, ROOM_H / 2, -ROOM_D / 2 - WALL_T / 2)),
    ('wall_left',  (WALL_T, ROOM_H, ROOM_D), (-ROOM_W / 2 - WALL_T / 2, ROOM_H / 2, 0)),
    ('wall_right', (WALL_T, ROOM_H, ROOM_D), (ROOM_W / 2 + WALL_T / 2, ROOM_H / 2, 0)),
]
for i, (name, size, pos) in enumerate(walls):
    make_wall(name, size, pos, i * 200, 200)

# ------------------------------------------------------------ floor screen
screen_geo = base.create(geometryCOMP, 'screen_geo')
screen_geo.nodeX, screen_geo.nodeY = 1000, 200
for child in screen_geo.children:
    child.destroy()
rect = screen_geo.create(rectangleSOP, 'rect1')
rect.par.sizex = SCREEN_W
rect.par.sizey = SCREEN_H
rect.display = True
rect.render = True
screen_geo.render = True
screen_geo.display = True
# Default rectangle is XY (vertical). Rotate -90 so it lies on the floor.
# Do not also set Orientation=ZX: that plus rx=-90 stands the screen on edge
# and it disappears in OUT (especially with a downward look-at).
screen_geo.par.rx = -90
screen_geo.par.ry = 0
screen_geo.par.rz = 0
screen_geo.par.tx = 0
screen_geo.par.ty = 0.05           # just above the floor to avoid z-fighting
screen_geo.par.tz = 0
screen_geo.par.material = screen_mat.path
set_first_par(screen_mat, ['colormap'], 'screen_level')
set_first_par(screen_mat, ['usecolormap', 'applycolormap', 'colormapon'], True)
set_first_par(screen_geo, ['cullface', 'cull'], 'off')
set_first_par(screen_geo, ['twosided'], True)

# ------------------------------------------------------------- trends data
table = base.create(tableDAT, 'trends_table')
table.nodeX, table.nodeY = 0, -200
table.clear()
table.appendRow(['query', 'search_volume', 'categories', 'trend_breakdown'])
for sample in ['國旅補助', 'the screen going on and off', '虛擬房間']:
    table.appendRow([sample, '0', '', ''])

trend_index = base.create(constantCHOP, 'trend_index')
trend_index.nodeX, trend_index.nodeY = 200, -200
trend_index.par.name0 = 'index'
trend_index.par.value0 = 0

# ---------------------------------------------------------- on/off rhythm
pulse = base.create(lfoCHOP, 'pulse')
pulse.nodeX, pulse.nodeY = 400, -200
set_first_par(pulse, ['type', 'wavetype', 'waveform'], 'square')
set_first_par(pulse, ['frequency', 'freq', 'rate'], 1.0 / PULSE_PERIOD)
set_first_par(pulse, ['amp', 'amplitude', 'gain'], 0.5)
set_first_par(pulse, ['offset', 'off'], 0.5)   # square wave between 0 and 1

cycler = base.create(chopexecuteDAT, 'trend_cycler')
cycler.nodeX, cycler.nodeY = 600, -200
set_first_par(cycler, ['chop'], 'pulse')
set_first_par(cycler, ['offtoon'], True)
set_first_par(cycler, ['valuechange', 'onvaluechange'], False)
cycler.text = '''# Advances to the next trend each time the screen turns on.
# Stubs are required: newer TD errors if an enabled callback is missing.

def onOffToOn(channel, sampleIndex, val, prev):
    table = op('trends_table')
    n = max(1, table.numRows - 1)
    idx = op('trend_index')
    idx.par.value0 = (int(idx.par.value0) + 1) % n
    return

def onOnToOff(channel, sampleIndex, val, prev):
    return

def onWhileOn(channel, sampleIndex, val, prev):
    return

def onWhileOff(channel, sampleIndex, val, prev):
    return

def onValueChange(channel, sampleIndex, val, prev):
    return
'''

# ----------------------------------------------------------- screen image
screen_text = base.create(textTOP, 'screen_text')
screen_text.nodeX, screen_text.nodeY = 0, 0
set_first_par(screen_text, ['resolutionw', 'resw'], 1280)
set_first_par(screen_text, ['resolutionh', 'resh'], 720)
set_first_par(screen_text, ['fontsizex', 'fontsize'], 110)
set_first_par(screen_text, ['alignx'], 'center')
set_first_par(screen_text, ['aligny'], 'center')
set_first_par(screen_text, ['fontcolorr', 'fontr'], 1)
set_first_par(screen_text, ['fontcolorg', 'fontg'], 1)
set_first_par(screen_text, ['fontcolorb', 'fontb'], 1)
set_first_par(screen_text, ['bgcolorr', 'bgr'], 0)
set_first_par(screen_text, ['bgcolorg', 'bgg'], 0)
set_first_par(screen_text, ['bgcolorb', 'bgb'], 0)
set_first_par(screen_text, ['bgalpha', 'bga', 'bgalpha1'], 1)
try:
    screen_text.par.font = 'Microsoft JhengHei'   # CJK-capable font on Windows
except Exception:
    print('build_virtual_room: set a CJK font on screen_text manually')
# Column 0 is "query". Avoid name lookup — it fails on some TD builds.
text_par = get_par(screen_text, 'text')
if text_par is not None:
    text_par.expr = (
        "str(op('trends_table')["
        "int(op('trend_index')[0]) % max(1, op('trends_table').numRows - 1) + 1,"
        " 0]) if op('trends_table').numRows > 1 else 'TRENDING'"
    )

screen_level = base.create(levelTOP, 'screen_level')
screen_level.nodeX, screen_level.nodeY = 200, 0
screen_level.inputConnectors[0].connect(screen_text)
# Fade RGB to black when off. Do not use opacity — that makes the floor show through.
set_first_par(screen_level, ['opacity', 'opacity1'], 1)
set_first_par_expr(screen_level, ['brightness1', 'bright1', 'gain1'], ONOFF)
set_first_par(screen_mat, ['usealpha', 'applyalpha', 'alphamapon'], False)

# ------------------------------------------------------ light from screen
light = base.create(lightCOMP, 'screen_light')
light.nodeX, light.nodeY = 1200, 200
set_first_par(light, ['lighttype', 'type'], 'point')
light.par.tx = 0
light.par.ty = 0.35                # just above the floor screen
light.par.tz = 0
set_first_par_expr(light, ['dimmer', 'intensity'], ONOFF + ' * 0.35')
set_first_par(light, ['attenuate', 'atten'], True)
set_first_par(light, ['quadatten', 'atten2', 'rolloff'], 0.8)

# --------------------------------------------------------- camera + render
cam = base.create(cameraCOMP, 'cam1')
cam.nodeX, cam.nodeY = 1400, 200
cam.par.tx = 0
cam.par.ty = 1.6                   # standing eye height, looking straight down
cam.par.tz = 0
cam.par.rx = -90
cam.par.ry = 0
cam.par.rz = 0
set_first_par(cam, ['lookat', 'lookatpath'], '')
set_first_par(cam, ['fov', 'fovx'], 70)

render = base.create(renderTOP, 'render1')
render.nodeX, render.nodeY = 400, 0
set_first_par(render, ['resolutionw', 'resw'], 1920)
set_first_par(render, ['resolutionh', 'resh'], 1080)
render.par.camera = 'cam1'
render.par.geometry = '*'
render.par.lights = 'screen_light'
set_first_par(render, ['bgcolorr', 'bgr'], 0)
set_first_par(render, ['bgcolorg', 'bgg'], 0)
set_first_par(render, ['bgcolorb', 'bgb'], 0)
set_first_par(render, ['ambr', 'ambientr'], 0)
set_first_par(render, ['ambg', 'ambientg'], 0)
set_first_par(render, ['ambb', 'ambientb'], 0)

out_level = base.create(levelTOP, 'out_level')
out_level.nodeX, out_level.nodeY = 500, 0
out_level.inputConnectors[0].connect(render)
set_first_par_expr(out_level, ['brightness1', 'bright1', 'gain1'], ONOFF)
set_first_par(out_level, ['opacity', 'opacity1'], 1)

out = base.create(nullTOP, 'OUT')
out.nodeX, out.nodeY = 600, 0
out.inputConnectors[0].connect(out_level)
out.viewer = True

print('build_virtual_room: done -> {}'.format(base.path))
print('Fullscreen {}/OUT on the real screen (e.g. via a Window COMP).'.format(base.path))
