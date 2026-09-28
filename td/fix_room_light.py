r"""Make the virtual room black when the screen is off, and lit only by
the floor-screen light when it is on.

Does NOT rebuild or delete trends_loader.

In the Textport:
  exec(open(r"C:\Users\YOURNAME\Documents\daily-trends-touchdesigner\td\fix_room_light.py", encoding="utf-8").read())
"""

BASE = '/project1/virtual_room'
# Hard on/off (square LFO can sit slightly above 0).
ONOFF = "1 if op('pulse')[0] > 0.5 else 0"
# How bright the walls get when the screen is on. Lower if walls blow out.
LIGHT_WHEN_ON = 0.35
WALL_DIFFUSE = 0.12


def par(node, name):
    try:
        return node.par[name]
    except Exception:
        try:
            return getattr(node.par, name)
        except Exception:
            return None


def setp(node, names, value):
    for n in names:
        p = par(node, n)
        if p is None:
            continue
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


def setx(node, names, expr):
    for n in names:
        p = par(node, n)
        if p is None:
            continue
        try:
            p.expr = expr
            return True
        except Exception:
            continue
    return False


base = op(BASE)
if base is None:
    raise RuntimeError('Not found: ' + BASE)

mat = base.op('room_mat')
if mat is not None:
    # Walls have no self-glow and no ambient fill — only the screen light.
    for names in (
        ['ambr', 'ambientr'],
        ['ambg', 'ambientg'],
        ['ambb', 'ambientb'],
        ['emitr', 'emissionr', 'emit'],
        ['emitg', 'emissiong'],
        ['emitb', 'emissionb'],
        ['specr', 'specularr'],
        ['specg', 'specularg'],
        ['specb', 'specularb'],
    ):
        setp(mat, names, 0)
    # Diffuse must go to 0 when off. Unlit phong still shows base color as grey.
    setx(mat, ['diffr', 'diffuser'], ONOFF + '*{}'.format(WALL_DIFFUSE))
    setx(mat, ['diffg', 'diffuseg'], ONOFF + '*{}'.format(WALL_DIFFUSE))
    setx(mat, ['diffb', 'diffuseb'], ONOFF + '*{}'.format(WALL_DIFFUSE))
    setp(mat, ['useenvmap', 'envlight', 'environment'], False)

text = base.op('screen_text')
if text is not None:
    setp(text, ['bgcolorr', 'bgr'], 0)
    setp(text, ['bgcolorg', 'bgg'], 0)
    setp(text, ['bgcolorb', 'bgb'], 0)
    setp(text, ['bgalpha', 'bga', 'bgalpha1'], 1)

level = base.op('screen_level')
if level is not None:
    setp(level, ['opacity', 'opacity1'], 1)
    setx(level, ['brightness1', 'bright1', 'gain1'], ONOFF)

smat = base.op('screen_mat')
if smat is not None:
    setp(smat, ['usealpha', 'applyalpha', 'alphamapon'], False)

light = base.op('screen_light')
if light is not None:
    setp(light, ['lighttype', 'type'], 'point')
    light.par.tx = 0
    light.par.ty = 0.35          # just above the floor screen
    light.par.tz = 0
    setp(light, ['cr', 'colorr', 'lightr'], 1)
    setp(light, ['cg', 'colorg', 'lightg'], 1)
    setp(light, ['cb', 'colorb', 'lightb'], 1)
    setx(light, ['dimmer', 'intensity'], '{} * {}'.format(ONOFF, LIGHT_WHEN_ON))
    setp(light, ['attenuate', 'atten', 'attenuation'], True)
    setp(light, ['constatten', 'atten0'], 0)
    setp(light, ['linatten', 'atten1'], 0)
    setp(light, ['quadatten', 'atten2', 'rolloff'], 0.8)

rend = base.op('render1')
if rend is not None:
    setp(rend, ['bgcolorr', 'bgr'], 0)
    setp(rend, ['bgcolorg', 'bgg'], 0)
    setp(rend, ['bgcolorb', 'bgb'], 0)
    setp(rend, ['bgcolora', 'bga', 'bgalpha'], 1)
    setp(rend, ['ambr', 'ambientr'], 0)
    setp(rend, ['ambg', 'ambientg'], 0)
    setp(rend, ['ambb', 'ambientb'], 0)
    rend.par.lights = 'screen_light'   # only the screen light, no default fill

# Multiply the finished frame to black when off (opacity=0 would look grey).
out = base.op('OUT')
lvl = base.op('out_level')
if lvl is None and rend is not None:
    lvl = base.create(levelTOP, 'out_level')
    lvl.nodeX, lvl.nodeY = 500, 0
if lvl is not None and rend is not None:
    if lvl.inputs:
        lvl.inputConnectors[0].disconnect()
    lvl.inputConnectors[0].connect(rend)
    setx(lvl, ['brightness1', 'bright1', 'gain1'], ONOFF)
    setp(lvl, ['opacity', 'opacity1'], 1)
if out is not None and lvl is not None:
    if out.inputs:
        out.inputConnectors[0].disconnect()
    out.inputConnectors[0].connect(lvl)

print('fix_room_light: off = full black, on = walls lit from the floor screen.')
print('fix_room_light: raise LIGHT_WHEN_ON in this script if the walls are too dim.')
