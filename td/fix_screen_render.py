r"""Patch an existing /project1/virtual_room so the floor screen shows in OUT.

Does NOT rebuild or delete trends_loader / trends_table.

In the Textport:
  exec(open(r"C:\Users\YOURNAME\Documents\daily-trends-touchdesigner\td\fix_screen_render.py", encoding="utf-8").read())
"""

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


base = op(BASE)
if base is None:
    raise RuntimeError('Not found: ' + BASE)

geo = base.op('screen_geo')
rect = geo.op('rect1') if geo else None
mat = base.op('screen_mat')
cam = base.op('cam1')
level = base.op('screen_level')

if geo is None or rect is None:
    raise RuntimeError('screen_geo/rect1 missing')

geo.render = True
geo.display = True
rect.render = True
rect.display = True

# Absolute material path (../screen_mat can fail depending on cwd of the geo).
if mat is not None:
    geo.par.material = mat.path
    setp(mat, ['colormap'], 'screen_level' if level is None else level.path)
    setp(mat, ['usecolormap', 'applycolormap', 'colormapon'], True)
    setp(mat, ['cullface', 'cull'], 'off')
    setp(mat, ['twosided', 'doubleface'], True)

# Default rectangle is XY (vertical). Rotate -90 onto the floor.
# Auto Orientation=ZX + look-at from above made the screen edge-on after git pull.
geo.par.rx = -90
geo.par.ry = 0
geo.par.rz = 0
geo.par.tx = 0
geo.par.ty = 0.05
geo.par.tz = 0

# Two-sided so a flipped normal still shows the texture.
setp(geo, ['cullface', 'cull'], 'off')
setp(geo, ['twosided'], True)

# Aim the camera down at the floor screen (horizontal view only sees a sliver).
if cam is not None:
    cam.par.tx = 0
    cam.par.ty = 1.6
    cam.par.tz = 0
    setp(cam, ['lookat', 'lookatpath'], '')
    cam.par.rx = -90
    cam.par.ry = 0
    cam.par.rz = 0
    setp(cam, ['fov', 'fovx'], 70)

print('fix_screen_render: material=', geo.par.material, 'rx=', geo.par.rx)
print('fix_screen_render: check OUT — you should see the floor screen facing the camera.')
