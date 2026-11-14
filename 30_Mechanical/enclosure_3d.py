"""3D model of the enclosure -> shell.stl, lid.stl, button_cap.stl (print orientation, mm).

Run: python enclosure_3d.py      (needs: pip install manifold3d numpy)
Parameters come from enclosure_drawing.py (PCB coordinates; z = height above PCB top, + = front).
Before writing the STLs it checks that no part (PCB, modules, battery, pins, plugs) collides with the print.
"""
import struct
import numpy as np
from manifold3d import Manifold, CrossSection, JoinType
from enclosure_drawing import *  # noqa: F403  shared parameters

SEG = 48
E = 0.01                      # overlap so booleans never leave zero-thickness skins
INSERT_D, INSERT_DEPTH = 4.2, 7.0     # M3 heat-set insert hole in the front bosses
SCREW_D, HEAD_D, HEAD_DEPTH = 3.4, 6.2, 1.2
SPACER_D = 6.0
LIP, LIP_H, LIP_GAP = 1.0, 2.0, 0.25  # locating lip on the lid
TRAY_H = 4.5
CAP_D, CAP_FLANGE_D, CAP_PROUD = 8.0, 10.5, 1.0
TACT_TOP = 5.0                # tact switch plunger top above the PCB (6x6 mm, H = 5 mm type)
NUT_Y1 = OY1 - NUT_WALL       # nut slot in the plinth, PCB y
NUT_Y0 = NUT_Y1 - NUT_T
BATT_Y = (79.0, 114.0)        # battery y range (PCB coords); x from BATT
BX0, BX1 = BATT[0], BATT[2]


# ---- helpers: PCB coords (x right, y down) -> model coords (x right, y up, z front)
def box(x0, y0, x1, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0 - OX0, OY1 - y1, z0])


def cyl(x, y, d, z0, z1):
    return Manifold.cylinder(z1 - z0, d / 2, d / 2, SEG).translate([x - OX0, OY1 - y, z0])


def rounded(x0, y0, x1, y1, r, z0, z1):
    cs = CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]).translate([r, r]).offset(r, JoinType.Round, 2.0, SEG)
    return Manifold.extrude(cs, z1 - z0).translate([x0 - OX0, OY1 - y1, z0])


def union(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out + p
    return out


CAV = (PCB[0] - GAP, PCB[1] - GAP, PCB[2] + GAP, PCB[3] + GAP)
uw, uh, uz = USB_CUT
sw, sh, sz = SW_CUT

# =============================== SHELL =======================================
shell = rounded(OX0, OY0, OX1, OY1, R, Z_LID_IN, Z_FRONT_OUT)
shell -= box(CAV[0], CAV[1], CAV[2], CAV[3], Z_LID_IN - E, Z_FRONT_IN)                       # cavity
shell += union([cyl(x, y, BOSS_D, 0, Z_FRONT_IN + E) for x, y in HOLES])                    # bosses
cuts = [cyl(x, y, INSERT_D, -E, INSERT_DEPTH) for x, y in HOLES]                            # insert holes
cuts.append(box(WINDOW[0], WINDOW[1], WINDOW[2], WINDOW[3], Z_FRONT_IN - E, Z_FRONT_OUT + E))  # display window
cuts.append(box(RADAR[0] - 1, RADAR[1] - 1, RADAR[2] + 1, RADAR[3] + 1, Z_FRONT_IN - E, Z_FRONT_OUT - RADOME))  # radome
cuts += [cyl(x, y, BTN_HOLE, Z_FRONT_IN - E, Z_FRONT_OUT + E) for x, y in BUTTONS]
cuts.append(box(USB_X - uw / 2, OY0 - E, USB_X + uw / 2, CAV[1] + E, uz - uh / 2, uz + uh / 2))   # USB-C
cuts.append(box(SWITCH_X - sw / 2, OY0 - E, SWITCH_X + sw / 2, CAV[1] + E, Z_LID_IN - E, sz + sh / 2))  # SW1 slot, open to back
cuts.append(box(CX - NUT_AF / 2, NUT_Y0, CX + NUT_AF / 2, NUT_Y1, Z_LID_IN - E, NUT_Z + 6.6))      # nut slot from the back
cuts.append(Manifold.cylinder(NUT_WALL + 2 * E, TRIPOD_HOLE / 2, TRIPOD_HOLE / 2, SEG)
            .rotate([90, 0, 0]).translate([CX - OX0, NUT_WALL + E, NUT_Z]))                 # tripod screw hole
cuts.append(box(GROOVE[0], CAV[3] - E, GROOVE[1], CAV[3] + GROOVE[2], Z_LID_IN - E, 6.0))    # battery wire groove
shell -= union(cuts)

# =============================== LID =========================================
lid = rounded(OX0, OY0, OX1, OY1, R, Z_BACK_OUT, Z_LID_IN)
g = LIP_GAP
ring = box(CAV[0] + g, CAV[1] + g, CAV[2] - g, CAV[3] - g, Z_LID_IN - E, Z_LID_IN + LIP_H) \
    - box(CAV[0] + g + LIP, CAV[1] + g + LIP, CAV[2] - g - LIP, CAV[3] - g - LIP, Z_LID_IN - 1, Z_LID_IN + LIP_H + 1)
ring -= box(GROOVE[0] - 0.5, CAV[3] - 3, GROOVE[1] + 0.5, CAV[3] + 1, Z_LID_IN, Z_LID_IN + LIP_H + 1)   # wire passes the lip
lid += ring
lid += union([cyl(x, y, SPACER_D, Z_LID_IN - E, Z_PCB_BOT) for x, y in HOLES])                # spacer tubes
tw = TRAY_WALL
tray = box(BX0 - tw, BATT_Y[0] - tw, BX1 + tw, BATT_Y[1] + tw, Z_LID_IN - E, Z_LID_IN + TRAY_H) \
    - box(BX0, BATT_Y[0], BX1, BATT_Y[1], Z_LID_IN - 1, Z_LID_IN + TRAY_H + 1)
tray -= box(BX1 - 1, BATT_Y[1] - 8, BX1 + tw + 1, BATT_Y[1] - 2, Z_LID_IN, Z_LID_IN + TRAY_H + 1)      # wire exit
lid += tray
lid += box(SWITCH_X - sw / 2 + 0.25, OY0, SWITCH_X + sw / 2 - 0.25, CAV[1], Z_LID_IN - E, -0.5)       # tongue closing the SW1 slot
lid -= union([cyl(x, y, SCREW_D, Z_BACK_OUT - E, Z_PCB_BOT + E) for x, y in HOLES]
             + [cyl(x, y, HEAD_D, Z_BACK_OUT - E, Z_BACK_OUT + HEAD_DEPTH) for x, y in HOLES])

# =============================== BUTTON CAP ==================================
cap_top = Z_FRONT_OUT + CAP_PROUD


def button_cap(x, y):
    c = cyl(x, y, CAP_D, TACT_TOP, cap_top) + cyl(x, y, CAP_FLANGE_D, Z_FRONT_IN - 1.2, Z_FRONT_IN - 0.2)
    return c - cyl(x, y, 3.8, TACT_TOP - E, TACT_TOP + 1.0)       # seat on the plunger


caps = [button_cap(x, y) for x, y in BUTTONS]

# =============================== FIT CHECK ===================================
DISP_PCB = (175.01, 83.83, 253.01, 109.73)
keepout = {
    'PCB': box(PCB[0], PCB[1], PCB[2], PCB[3], Z_PCB_BOT, 0),
    'display socket+header': box(250.1, 86.6, 252.7, 107.0, 0, 11.0),
    'display PCB': box(*DISP_PCB, 11.0, 12.6),
    'display panel': box(GLASS[0], GLASS[1], GLASS[2], GLASS[3], 12.6, 15.0),
    'radar socket': box(148.0, 93.2, 150.5, 100.8, 0, 8.5),
    'radar module': box(RADAR[0], RADAR[1], RADAR[2], RADAR[3], 8.5, 14.6),
    'XIAO + USB-C': box(209.6, 74.69, 230.75, 98.19, 0, 4.4),
    'USB plug': box(USB_X - 6.0, OY0 - 15, USB_X + 6.0, 75, uz - 3.25, uz + 3.25),
    'shield can U9 (height assumed 4)': box(158.74, 87.56, 205.6, 120.94, 0, 4.0),
    'SW1 body': box(231.05, 75.0, 242.45, 80.2, 0, 4.4),
    'SW1 lever + travel': box(SWITCH_X - 2.2, 70.8, SWITCH_X + 2.2, 75.0, 0.5, 4.0),
    'J5 header': box(198.8, 75.45, 206.16, 78.55, 0, 6.0),
    'J3 + battery plug': box(231.5, 114.05, 246.3, 120.95, 0, 5.0),
    'tact switches': box(209.75, 113.75, 216.25, 120.25, 0, 3.6) + box(220.75, 113.75, 227.25, 120.25, 0, 3.6),
    'tall parts (C12-C14, L1, Q3, Q4, TP9)': box(227.7, 96.0, 250.6, 113.9, 0, 5.5),
    'battery 503450': box(BX0 + 0.2, BATT_Y[0] + 0.2, BX1 - 0.2, BATT_Y[1] - 0.2, Z_LID_IN + 0.05, Z_LID_IN + 5.2),
    'THT pin tips (back)': union([box(*b, Z_PCB_BOT - 2.5, Z_PCB_BOT) for b in [
        (209.0, 114.0, 228.0, 120.0), (243.6, 115.7, 245.3, 119.3), (250.6, 87.0, 252.3, 106.6),
        (199.0, 76.2, 206.0, 77.8), (231.8, 76.7, 241.8, 78.3), (148.4, 93.6, 150.1, 100.4), (177.4, 91.4, 179.1, 93.1)]]),
    '1/4" nut': box(CX - 5.56, NUT_Y0 + 0.1, CX + 5.56, NUT_Y1 - 0.1, NUT_Z - 6.4, NUT_Z + 6.4),
    'button caps': union(caps),
}
printed = {'shell': shell, 'lid': lid, 'caps': union(caps)}


def check():
    ok = True
    for pname, p in printed.items():
        assert p.status().name == 'NoError' and p.volume() > 0, pname
        for kname, k in keepout.items():
            if pname == 'caps' and kname == 'button caps':
                continue
            v = (p ^ k).volume()
            if v > 0.01:
                ok = False
                print(f'COLLISION {pname} x {kname}: {v:.2f} mm3')
    v = (shell ^ lid).volume()
    if v > 0.01:
        ok = False
        print(f'COLLISION shell x lid: {v:.2f} mm3')
    # clearances worth knowing
    print(f'display glass -> window inner face: {Z_FRONT_IN - 15.0:.1f} mm   radar antenna -> radome: {Z_FRONT_OUT - RADOME - 14.6:.1f} mm')
    print(f'battery top -> THT pin tips: {(Z_PCB_BOT - 2.5) - (Z_LID_IN + 5.2):.1f} mm   screw: M3x16 (head seat to insert end {HEAD_DEPTH - 2 - Z_LID_IN + INSERT_DEPTH - 1.2:.1f})')
    return ok


def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    t = v[np.asarray(mesh.tri_verts)]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    with open(path, 'wb') as f:
        f.write(b'MAR07 SpeedRadar enclosure'.ljust(80, b' ') + struct.pack('<I', len(t)))
        for i in range(len(t)):
            f.write(struct.pack('<12fH', *n[i], *t[i].ravel(), 0))
    bb = m.bounding_box()
    print(f'{path}: {len(t)} triangles, {bb[3] - bb[0]:.1f} x {bb[4] - bb[1]:.1f} x {bb[5] - bb[2]:.1f} mm, {m.volume() / 1000:.1f} cm3')


def flip_to_bed(m):
    """Front face down on the print bed."""
    m = m.rotate([180, 0, 0])
    bb = m.bounding_box()
    return m.translate([-bb[0], -bb[1], -bb[2]])


if __name__ == '__main__':
    import os
    assert check(), 'fit check failed, no STL written'
    print('fit check OK')
    d = os.path.dirname(os.path.abspath(__file__))
    write_stl(flip_to_bed(shell), os.path.join(d, 'shell.stl'))
    write_stl(lid.translate([0, 0, -Z_BACK_OUT]), os.path.join(d, 'lid.stl'))
    write_stl(flip_to_bed(caps[0]), os.path.join(d, 'button_cap.stl'))
