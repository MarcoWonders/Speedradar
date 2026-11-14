"""2D drawing of the 3D printed enclosure (v0 concept). Run: python enclosure_drawing.py -> enclosure_v0.svg

All X/Y values are KiCad PCB coordinates (mm) so features line up with the board file.
Z is height above the PCB top surface (+ = towards the front / display side).
Values marked 'measure' are estimates; check them on the real parts before printing.
"""
import math
from html import escape

# ---------------- PCB (from MAR07_SpeedRadar.kicad_pcb) ----------------------
PCB = (144, 75, 255, 124)                                 # x0, y0, x1, y1 -> 111 x 49
HOLES = [(148, 79), (251, 79), (148, 120), (251, 120)]   # M3
BUTTONS = [(213, 117), (224, 117)]                        # SW3 / SW2 centres
RADAR = (148.0, 84.5, 173.0, 109.5)                       # CDM324 outline (J1)
GLASS = (179.73, 84.59, 249.57, 108.97)                   # display glass (J4), measure
WINDOW = (183.5, 85.6, 248.5, 107.9)                      # active area + ~0.5, FPC end is left, measure
USB_X = 220.5                                             # XIAO (U3) USB-C at the top edge
SWITCH_X = 236.75                                         # SW1 angled OS102011MA1Q lever centre (pin 2) at the top edge
J3_PLUG = (231.5, 115.0, 237.7, 120.0)                    # JST-PH plug, inserted from the left

# battery: LiPo 503450 (5 x 34 x 50, ~1000 mAh) in a tray on the back lid, behind the right half
BATT = (183.5, 80.0, 234.5, 115.0)                        # cell incl. protection PCB (~51 x 35)
TRAY_WALL = 0.8
GROOVE = (229.0, 233.0, 2.5)                              # x0, x1, depth: wire channel in the plinth under the PCB edge

# ---------------- enclosure parameters ---------------------------------------
WALL, GAP, R = 2.0, 0.5, 3.0          # wall, PCB clearance, outer corner radius
PLINTH = 10.0                         # solid bottom block carrying the tripod nut
Z_FRONT_IN = 16.5                     # front wall inner face above PCB top (module stack ~15-16, measure)
Z_PCB_BOT = -1.6
Z_LID_IN = -10.5                      # leaves ~6.4 mm for a 5 mm LiPo (e.g. 503450) + THT pins
Z_FRONT_OUT, Z_BACK_OUT = Z_FRONT_IN + WALL, Z_LID_IN - WALL
RADOME = 1.0                          # front wall thinned to 1 mm over the radar, no infill gaps
BTN_HOLE = 8.5
BOSS_D = 7.0                          # Ø4.2 insert hole leaves 1.4 mm wall
NUT_AF, NUT_T, TRIPOD_HOLE = 11.4, 5.8, 6.5   # 1/4"-20 hex nut pocket (11.11 AF, 5.56 thick)
USB_CUT = (12.5, 7.0, 2.8)            # w, h, centre z (USB-C plug overmold clearance)
SW_CUT = (7.5, 4.0, 2.2)              # w, h, centre z (lever slot; open to the back so the PCB can drop in)
NUT_WALL = 2.0                        # plinth material under the nut (tripod screw must reach the nut)

# derived outer box (front view, PCB coordinates)
OX0, OY0 = PCB[0] - GAP - WALL, PCB[1] - GAP - WALL
OX1 = PCB[2] + GAP + WALL
CAV_Y1 = PCB[3] + GAP
OY1 = CAV_Y1 + PLINTH
W, H, D = OX1 - OX0, OY1 - OY0, Z_FRONT_OUT - Z_BACK_OUT
CX = (OX0 + OX1) / 2
NUT_Z = (Z_FRONT_IN + Z_LID_IN) / 2

# ---------------- sheet layout (A3, mm) --------------------------------------
X0, Y0 = 30, 85                # front view: outer top-left
XR = X0 + W + 25               # right view: front face x
YT = Y0 - 18                   # top view: front face y
YB = Y0 + H + 18               # bottom view: front face y
fx = lambda x: X0 + (x - OX0)
fy = lambda y: Y0 + (y - OY0)
tz = lambda z: YT - (Z_FRONT_OUT - z)
bz = lambda z: YB + (Z_FRONT_OUT - z)
rz = lambda z: XR + (Z_FRONT_OUT - z)

out = []
S = lambda s: out.append(s)
LINE = 'stroke="#000" fill="none" stroke-width="0.35"'
THIN = 'stroke="#000" fill="none" stroke-width="0.18"'
HID = 'stroke="#000" fill="none" stroke-width="0.18" stroke-dasharray="1.5 0.8"'
CEN = 'stroke="#c00" fill="none" stroke-width="0.13" stroke-dasharray="4 1 0.6 1"'
PROP = 'stroke="#d06000" fill="#d0600022" stroke-width="0.3"'
DIM = 'stroke="#0050a0" fill="none" stroke-width="0.13"'


def rect(x0, y0, x1, y1, st=LINE, r=0):
    S(f'<rect x="{min(x0, x1):.2f}" y="{min(y0, y1):.2f}" width="{abs(x1 - x0):.2f}" height="{abs(y1 - y0):.2f}" rx="{r}" {st}/>')


def circ(x, y, d, st=LINE):
    S(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{d / 2:.2f}" {st}/>')


def line(x0, y0, x1, y1, st=THIN):
    S(f'<line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x1:.2f}" y2="{y1:.2f}" {st}/>')


def text(x, y, s, size=2.5, anchor='start', color='#000', rot=0, bold=False):
    tr = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ''
    w = ' font-weight="bold"' if bold else ''
    S(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" fill="{color}"{w}{tr} '
      f'font-family="Arial, sans-serif">{escape(s)}</text>')


def hexagon(x, y, af, st):
    r = af / math.sqrt(3)
    pts = ' '.join(f'{x + r * math.cos(math.radians(a)):.2f},{y + r * math.sin(math.radians(a)):.2f}' for a in range(0, 360, 60))
    S(f'<polygon points="{pts}" {st}/>')


def cross(x, y, s=2.5):
    line(x - s, y, x + s, y, CEN); line(x, y - s, x, y + s, CEN)


def dim_h(x0, x1, y, label, ext_from=None):
    for x in (x0, x1):
        line(x, (ext_from if ext_from is not None else y) , x, y + (1 if ext_from is None or ext_from < y else -1), DIM)
    line(x0, y, x1, y, DIM)
    for x, d in ((x0, 1), (x1, -1)):
        S(f'<polygon points="{x:.2f},{y:.2f} {x + 1.6 * d:.2f},{y - 0.5:.2f} {x + 1.6 * d:.2f},{y + 0.5:.2f}" fill="#0050a0"/>')
    text((x0 + x1) / 2, y - 0.8, label, 2.2, 'middle', '#0050a0')


def dim_v(y0, y1, x, label, ext_from=None):
    for y in (y0, y1):
        line(ext_from if ext_from is not None else x, y, x + (1 if ext_from is None or ext_from < x else -1), y, DIM)
    line(x, y0, x, y1, DIM)
    for y, d in ((y0, 1), (y1, -1)):
        S(f'<polygon points="{x:.2f},{y:.2f} {x - 0.5:.2f},{y + 1.6 * d:.2f} {x + 0.5:.2f},{y + 1.6 * d:.2f}" fill="#0050a0"/>')
    text(x - 0.8, (y0 + y1) / 2, label, 2.2, 'middle', '#0050a0', -90)


# =============================== FRONT VIEW ==================================
text(fx(OX0), fy(OY0) - 4 + 0, '', 2)
rect(fx(OX0), fy(OY0), fx(OX1), fy(OY1), LINE, R)
rect(fx(WINDOW[0]), fy(WINDOW[1]), fx(WINDOW[2]), fy(WINDOW[3]), LINE, 0.5)
rect(fx(GLASS[0]), fy(GLASS[1]), fx(GLASS[2]), fy(GLASS[3]), HID)
rect(fx(RADAR[0]), fy(RADAR[1]), fx(RADAR[2]), fy(RADAR[3]), HID)
text(fx((RADAR[0] + RADAR[2]) / 2), fy((RADAR[1] + RADAR[3]) / 2) - 1, 'RADOME', 2.2, 'middle')
text(fx((RADAR[0] + RADAR[2]) / 2), fy((RADAR[1] + RADAR[3]) / 2) + 2, f'wall {RADOME} mm', 2.0, 'middle')
text(fx((WINDOW[0] + WINDOW[2]) / 2), fy((WINDOW[1] + WINDOW[3]) / 2) + 1, 'DISPLAY WINDOW', 2.5, 'middle')
rect(fx(PCB[0]), fy(PCB[1]), fx(PCB[2]), fy(PCB[3]), HID)
line(fx(OX0), fy(CAV_Y1), fx(OX1), fy(CAV_Y1), HID)
for x, y in BUTTONS:
    circ(fx(x), fy(y), BTN_HOLE); cross(fx(x), fy(y), 5.5)
for x, y in HOLES:
    circ(fx(x), fy(y), BOSS_D, HID); cross(fx(x), fy(y))
rect(fx(CX - NUT_AF / 2), fy(OY1 - NUT_WALL - NUT_T), fx(CX + NUT_AF / 2), fy(OY1 - NUT_WALL), HID)
# battery tray (behind the PCB, on the lid) + wire path to J3
BAT = 'stroke="#7a3d00" fill="none" stroke-width="0.25" stroke-dasharray="2 0.8"'
rect(fx(BATT[0] - TRAY_WALL), fy(BATT[1] - TRAY_WALL), fx(BATT[2] + TRAY_WALL), fy(BATT[3] + TRAY_WALL), BAT)
text(fx(BATT[0]) + 1, fy(BATT[1]) + 3, 'battery tray (lid side)', 1.8, color='#7a3d00')
rect(fx(J3_PLUG[0]), fy(J3_PLUG[1]), fx(J3_PLUG[2]), fy(J3_PLUG[3]), BAT)
rect(fx(GROOVE[0]), fy(CAV_Y1), fx(GROOVE[1]), fy(CAV_Y1 + GROOVE[2]), BAT)
S(f'<polyline points="{fx(BATT[2]):.2f},{fy(BATT[3] - 3):.2f} {fx(GROOVE[0] + 2):.2f},{fy(BATT[3] - 3):.2f} '
  f'{fx(GROOVE[0] + 2):.2f},{fy(CAV_Y1 + 1):.2f}" stroke="#c00" fill="none" stroke-width="0.3"/>')
S(f'<polyline points="{fx(GROOVE[0] + 2):.2f},{fy(CAV_Y1 + 1):.2f} {fx(GROOVE[0] + 2):.2f},{fy(J3_PLUG[3] - 2.5):.2f} '
  f'{fx(J3_PLUG[0]):.2f},{fy(J3_PLUG[3] - 2.5):.2f}" stroke="#c00" fill="none" stroke-width="0.3" stroke-dasharray="0.8 0.5"/>')
text(fx(GROOVE[1]) + 1, fy(OY1) - 4.5, 'wire groove 4 x 2.5 under PCB edge', 1.8, color='#c00')
line(fx(CX), fy(OY0) - 2, fx(CX), fy(OY1) + 2, CEN)
text(fx(OX0), fy(OY0) - 10, 'FRONT VIEW', 3.5, bold=True)
# dimensions
dim_h(fx(OX0), fx(OX1), fy(OY1) + 9, f'{W:.0f}', fy(OY1))
dim_v(fy(OY0), fy(OY1), fx(OX0) - 9, f'{H:.0f}', fx(OX0))
dim_v(fy(OY0), fy(CAV_Y1), fx(OX0) - 4, f'{CAV_Y1 - OY0:.0f}', fx(OX0))
dim_h(fx(HOLES[0][0]), fx(HOLES[1][0]), fy(OY0) - 7, f'{HOLES[1][0] - HOLES[0][0]:.0f} (M3 bosses)', fy(HOLES[0][1]))
dim_v(fy(HOLES[0][1]), fy(HOLES[2][1]), fx(OX1) + 5, f'{HOLES[2][1] - HOLES[0][1]:.0f}', fx(HOLES[1][0]))
dim_h(fx(WINDOW[0]), fx(WINDOW[2]), fy(WINDOW[1]) - 2.5, f'{WINDOW[2] - WINDOW[0]:.1f}')
dim_v(fy(WINDOW[1]), fy(WINDOW[3]), fx(WINDOW[2]) - 3, f'{WINDOW[3] - WINDOW[1]:.1f}')
dim_h(fx(BUTTONS[0][0]), fx(BUTTONS[1][0]), fy(OY1) + 4, f'{BUTTONS[1][0] - BUTTONS[0][0]:.0f}', fy(BUTTONS[0][1]))
text(fx(BUTTONS[0][0]) - 5.5, fy(BUTTONS[0][1]) + 1, f'2x Ø{BTN_HOLE}', 2.2, 'end')
text(fx(OX0) + 1, fy(OY1) - 2, f'pos. relative to outer edge: x - {OX0}, y - {OY0} (PCB coords)', 1.8, color='#555')

# =============================== TOP VIEW (looking down) =====================
rect(fx(OX0), tz(Z_FRONT_OUT), fx(OX1), tz(Z_BACK_OUT), LINE, R)
line(fx(OX0), tz(Z_LID_IN), fx(OX1), tz(Z_LID_IN), HID)
line(fx(OX0), tz(0), fx(OX1), tz(0), HID); line(fx(OX0), tz(Z_PCB_BOT), fx(OX1), tz(Z_PCB_BOT), HID)
uw, uh, uz = USB_CUT
rect(fx(USB_X - uw / 2), tz(uz + uh / 2), fx(USB_X + uw / 2), tz(uz - uh / 2), LINE, 1)
text(fx(USB_X), tz(uz - uh / 2) - 1.5, f'USB-C {uw}x{uh}', 2.0, 'middle')
sw, sh, sz = SW_CUT
rect(fx(SWITCH_X - sw / 2), tz(sz + sh / 2), fx(SWITCH_X + sw / 2), tz(sz - sh / 2), LINE, 0.5)
text(fx(SWITCH_X) + 5, tz(sz - sh / 2) - 1.5, f'switch slot {sw}x{sh}', 2.0, 'start')
text(fx(OX1) + 2, tz(0) + 0.8, 'PCB', 2.0); text(fx(OX1) + 2, tz(Z_LID_IN) + 0.8, 'lid split', 2.0)
text(fx(OX0), tz(Z_BACK_OUT) - 16, 'TOP VIEW (front face at bottom)', 3.5, bold=True)
dim_v(tz(Z_FRONT_OUT), tz(Z_BACK_OUT), fx(OX0) - 4, f'{D:.0f}', fx(OX0))
dim_h(fx(OX0), fx(USB_X), tz(Z_BACK_OUT) - 7, f'{USB_X - OX0:.2f}', tz(Z_BACK_OUT))
dim_h(fx(OX0), fx(SWITCH_X), tz(Z_BACK_OUT) - 12, f'{SWITCH_X - OX0:.1f}', tz(Z_BACK_OUT))

# =============================== BOTTOM VIEW (looking up) ====================
rect(fx(OX0), bz(Z_FRONT_OUT), fx(OX1), bz(Z_BACK_OUT), LINE, R)
line(fx(OX0), bz(Z_LID_IN), fx(OX1), bz(Z_LID_IN), HID)
circ(fx(CX), bz(NUT_Z), TRIPOD_HOLE); hexagon(fx(CX), bz(NUT_Z), NUT_AF, HID); cross(fx(CX), bz(NUT_Z), 8)
text(fx(CX) + 9, bz(NUT_Z) + 1, f'1/4"-20 tripod: Ø{TRIPOD_HOLE} + nut slot {NUT_AF} x {NUT_T}, nut slides in from the back', 2.0)
text(fx(OX0), bz(Z_BACK_OUT) + 7, 'BOTTOM VIEW (front face at top)', 3.5, bold=True)
dim_h(fx(OX0), fx(CX), bz(Z_BACK_OUT) + 13, f'{CX - OX0:.0f}', bz(Z_BACK_OUT))
dim_v(bz(Z_FRONT_OUT), bz(NUT_Z), fx(OX0) - 4, f'{Z_FRONT_OUT - NUT_Z:.1f}', fx(OX0))

# =============================== RIGHT SIDE SECTION ==========================
# outer shell
rect(rz(Z_FRONT_OUT), fy(OY0), rz(Z_BACK_OUT), fy(OY1), LINE, R)
line(rz(Z_FRONT_IN), fy(OY0) + WALL, rz(Z_FRONT_IN), fy(CAV_Y1), HID)
line(rz(Z_LID_IN), fy(OY0), rz(Z_LID_IN), fy(OY1), THIN)
line(rz(Z_FRONT_OUT), fy(CAV_Y1), rz(Z_LID_IN), fy(CAV_Y1), HID)
# PCB
rect(rz(0), fy(PCB[1]), rz(Z_PCB_BOT), fy(PCB[3]), 'stroke="#060" fill="#0a03" stroke-width="0.25"')
# display module stack (socket 8.5 + header 2.5 + PCB 1.6 + panel 2.2)
rect(rz(0), fy(GLASS[1]) + 3, rz(8.5), fy(GLASS[1]) + 5.5, HID)
rect(rz(11.0), fy(GLASS[1] - 0.8), rz(12.6), fy(GLASS[3] + 0.8), 'stroke="#036" fill="#0362" stroke-width="0.2"')
rect(rz(12.6), fy(GLASS[1]), rz(14.8), fy(GLASS[3]), 'stroke="#036" fill="#03a4" stroke-width="0.2"')
# bosses
for y in (HOLES[0][1], HOLES[2][1]):
    rect(rz(Z_FRONT_IN), fy(y - BOSS_D / 2), rz(0), fy(y + BOSS_D / 2), HID)
    rect(rz(Z_PCB_BOT), fy(y - 2.5), rz(Z_LID_IN), fy(y + 2.5), HID)
    line(rz(Z_FRONT_IN), fy(y), rz(Z_BACK_OUT) + 0, fy(y), CEN)
# battery in lid tray: cell on the lid, ~1.7 mm air gap to the THT pin tips (~2 mm below the PCB)
bz0 = Z_LID_IN + 5.2
rect(rz(bz0), fy(BATT[1]), rz(Z_LID_IN), fy(BATT[3]), 'stroke="#7a3d00" fill="#7a3d0022" stroke-width="0.2"')
for y in (BATT[1] - TRAY_WALL, BATT[3]):
    rect(rz(bz0 + 0.5), fy(y), rz(Z_LID_IN), fy(y + TRAY_WALL), 'stroke="#7a3d00" fill="#7a3d00" stroke-width="0.1"')
line(rz(Z_PCB_BOT - 2.0), fy(PCB[1]), rz(Z_PCB_BOT - 2.0), fy(PCB[3]), 'stroke="#999" stroke-width="0.15" stroke-dasharray="0.6 0.6"')
text(rz(bz0 - 2.6), fy((BATT[1] + BATT[3]) / 2), 'LiPo 503450', 1.8, 'middle', '#7a3d00', -90)
# wire groove under the PCB edge
rect(rz(4.0), fy(CAV_Y1), rz(Z_LID_IN), fy(CAV_Y1 + GROOVE[2]), 'stroke="#c00" fill="none" stroke-width="0.2" stroke-dasharray="1 0.5"')
# nut pocket
rect(rz(NUT_Z + 6.6), fy(OY1 - NUT_WALL - NUT_T), rz(Z_LID_IN), fy(OY1 - NUT_WALL), HID)
rect(rz(NUT_Z + TRIPOD_HOLE / 2), fy(OY1 - NUT_WALL), rz(NUT_Z - TRIPOD_HOLE / 2), fy(OY1), HID)
text(rz(Z_FRONT_OUT), fy(OY0) - 3, 'RIGHT SIDE (section)', 3.5, bold=True)
dim_h(rz(Z_FRONT_OUT), rz(Z_BACK_OUT), fy(OY1) + 9, f'{D:.0f}', fy(OY1))
dim_h(rz(Z_FRONT_IN), rz(0), fy(OY1) + 4, f'{Z_FRONT_IN}', fy(CAV_Y1))
text(rz(14), fy(GLASS[1]) - 1.5, 'display', 1.8, 'middle', '#036')
text(rz(-0.8), fy(PCB[1]) - 1.5, 'PCB', 1.8, 'middle', '#060')
text(rz(Z_FRONT_OUT) - 1, fy(OY0) + 4, 'front', 1.8, 'end')
text(rz(Z_BACK_OUT) + 1, fy(OY0) + 4, 'lid', 1.8)

# =============================== NOTES + TITLE ===============================
notes = [
    'CONCEPT v0 - not yet validated. All dimensions in mm.',
    'X/Y match KiCad PCB coordinates; outer box = PCB 111x49 + 0.5 gap + 2.0 wall,',
    f'  plus a {PLINTH:.0f} mm solid plinth at the bottom for the tripod nut.',
    'Parts: front shell (front + side walls + plinth) and a flat back lid.',
    f'Assembly: 4x M3 heat-set inserts in Ø{BOSS_D} front bosses ({Z_FRONT_IN} high),',
    '  M3x16 screws from the back through lid spacer tubes and PCB holes.',
    f'Radome: front wall {RADOME} mm over the radar, solid infill, no metal/paint;',
    '  keep the antenna-to-wall gap small (<1 mm) or tune wall to ~3.8 mm (lambda/2 PLA).',
    'Display: window = active area + 0.5. Glass position from seller photo:',
    '  MEASURE the module before printing; FPC (wider border) is on the left.',
    'Buttons: 6 mm tact switch top ~5 mm above PCB -> printed caps with',
    f'  ~{Z_FRONT_IN - 5 + 2:.1f} mm stem and retaining flange, or 13 mm tall tact switches.',
    'Tripod: 1/4"-20 hex nut slides into a slot in the plinth from the back; the lid closes it.',
    'SW1 slot is open to the back (lever passes when the PCB drops in); a lid tongue fills it.',
    'Top face: USB-C (XIAO at top edge) and slot for the angled SW1 lever.',
    'Battery: LiPo 503450 (5x34x50, ~1000 mAh, ~6 h at ~150 mA) in a tray',
    '  on the lid (0.8 walls), held by a 1 mm foam pad. ~1.7 mm air gap to',
    '  the THT pin tips; Kapton over TP8 / back test pads as extra safety.',
    'Battery wire: from the cell along the lid to a 4 x 2.5 groove in the',
    '  plinth under the PCB edge (x 229-233), up the front of the PCB to the',
    '  J3 plug (enters from the left). Leave ~40 mm slack to open the lid.',
    'Radar sits in a 2.54 mm socket: set its height to the radome after fit.',
    'Stack (measure): display glass ~15, radar antenna ~16 above PCB top.',
]
nx, ny = 255, 30
text(nx, ny - 6, 'NOTES', 3.5, bold=True)
for i, n in enumerate(notes):
    text(nx, ny + i * 4.2, n, 2.3)
# title block
tb = (255, 250, 410, 287)
rect(*tb)
line(tb[0], 262, tb[2], 262); line(tb[0], 274, tb[2], 274); line(330, 262, 330, tb[3])
text(tb[0] + 3, 258, 'MAR07 SpeedRadar - enclosure', 5, bold=True)
text(tb[0] + 3, 269, 'Concept drawing v0 (2D)', 3)
text(334, 269, 'Material: PETG / PLA', 3)
text(tb[0] + 3, 281, f'Outer {W:.0f} x {H:.0f} x {D:.0f} mm', 3)
text(334, 281, 'Scale 1:1 on A3', 3)

if __name__ == '__main__':
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">'
           f'<rect width="420" height="297" fill="#fff"/><rect x="10" y="10" width="400" height="277" {THIN}/>'
           + ''.join(out) + '</svg>')
    open(__file__.replace('enclosure_drawing.py', 'enclosure_v0.svg'), 'w', encoding='utf8').write(svg)
    print(f'outer {W} x {H} x {D} mm, nut z {NUT_Z}')
