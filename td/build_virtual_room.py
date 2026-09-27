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
room_mat.par.diffr = room_mat.par.diffg = room_mat.par.diffb = 0.55

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
screen_geo.par.rx = -90            # lay flat on the floor, facing up
screen_geo.par.ty = 0.02           # just above the floor to avoid z-fighting
screen_geo.par.material = '../screen_mat'

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
cycler.par.chop = 'pulse'
cycler.par.offtoon = True
cycler.text = '''# Advances to the next trend each time the screen turns on.

def onOffToOn(channel, sampleIndex, val, prev):
    table = op('trends_table')
    n = max(1, table.numRows - 1)
    idx = op('trend_index')
    idx.par.value0 = (int(idx.par.value0) + 1) % n
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
try:
    screen_text.par.font = 'Microsoft JhengHei'   # CJK-capable font on Windows
except Exception:
    print('build_virtual_room: set a CJK font on screen_text manually')
screen_text.par.text.expr = (
    "str(op('trends_table')["
    "int(op('trend_index')[0]) % max(1, op('trends_table').numRows - 1) + 1,"
    " 'query']) if op('trends_table').numRows > 1 else 'TRENDING'"
)

screen_level = base.create(levelTOP, 'screen_level')
screen_level.nodeX, screen_level.nodeY = 200, 0
screen_level.inputConnectors[0].connect(screen_text)
set_first_par_expr(screen_level, ['opacity', 'opacity1'], "op('pulse')[0]")

# ------------------------------------------------------ light from screen
light = base.create(lightCOMP, 'screen_light')
light.nodeX, light.nodeY = 1200, 200
set_first_par(light, ['lighttype', 'type'], 'point')
light.par.ty = 1.2                 # hovering above the floor screen
set_first_par_expr(light, ['dimmer', 'intensity'], "op('pulse')[0]")

# --------------------------------------------------------- camera + render
cam = base.create(cameraCOMP, 'cam1')
cam.nodeX, cam.nodeY = 1400, 200
cam.par.ty = 1.6                   # eye height, looking into the open side
cam.par.tz = ROOM_D / 2 + 2.5

render = base.create(renderTOP, 'render1')
render.nodeX, render.nodeY = 400, 0
set_first_par(render, ['resolutionw', 'resw'], 1920)
set_first_par(render, ['resolutionh', 'resh'], 1080)
render.par.camera = 'cam1'
render.par.geometry = '*'
render.par.lights = '*'

out = base.create(nullTOP, 'OUT')
out.nodeX, out.nodeY = 600, 0
out.inputConnectors[0].connect(render)
out.viewer = True

print('build_virtual_room: done -> {}'.format(base.path))
print('Fullscreen {}/OUT on the real screen (e.g. via a Window COMP).'.format(base.path))
