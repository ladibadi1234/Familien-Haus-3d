import bpy, math, sys
from mathutils import Vector

# ---------- reset ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- materials ----------
def mat(name, color, rough=0.6, metal=0.0, transmission=0.0, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if transmission > 0:
        bsdf.inputs["Transmission Weight"].default_value = transmission
        bsdf.inputs["IOR"].default_value = 1.45
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_str
    return m

M = {
    "beige":  mat("Wand_Beige", (0.92, 0.87, 0.76), 0.8),
    "wood":   mat("Holz_Braun", (0.42, 0.26, 0.15), 0.7),
    "roof":   mat("Dach_Dunkelgrau", (0.07, 0.07, 0.08), 0.55),
    "white":  mat("Innen_Weiss", (0.92, 0.92, 0.90), 0.8),
    "floor_w":mat("Boden_Holz", (0.55, 0.38, 0.22), 0.45),
    "floor_t":mat("Boden_Fliesen", (0.82, 0.82, 0.80), 0.25),
    "glass":  mat("Glas", (0.85, 0.92, 0.95), 0.05, transmission=1.0),
    "frame":  mat("Fensterrahmen", (0.15, 0.15, 0.16), 0.4),
    "door":   mat("Tür_Braun", (0.33, 0.19, 0.10), 0.5),
    "garage": mat("Garagentor_Grau", (0.55, 0.56, 0.58), 0.5, metal=0.3),
    "grass":  mat("Rasen", (0.20, 0.42, 0.14), 0.9),
    "concrete": mat("Terrasse", (0.65, 0.63, 0.60), 0.8),
    "solar":  mat("Solarpanel", (0.03, 0.05, 0.12), 0.2, metal=0.6),
    "car":    mat("Auto_Lack", (0.15, 0.30, 0.55), 0.25, metal=0.6),
    "tire":   mat("Reifen", (0.05, 0.05, 0.05), 0.8),
    "sofa":   mat("Sofa", (0.35, 0.42, 0.50), 0.85),
    "table":  mat("Tisch_Holz", (0.45, 0.30, 0.17), 0.4),
    "bed":    mat("Bettwäsche", (0.88, 0.88, 0.86), 0.8),
    "bed2":   mat("Bettdecke_Blau", (0.30, 0.42, 0.60), 0.8),
    "fixture":mat("Sanitär_Weiss", (0.95, 0.95, 0.94), 0.2),
    "counter":mat("Küchenzeile", (0.90, 0.90, 0.88), 0.35),
    "worktop":mat("Arbeitsplatte", (0.20, 0.20, 0.21), 0.3),
    "ceiling":mat("Decke_Weiss", (0.94, 0.94, 0.92), 0.85),
    "leaf":   mat("Blätter", (0.15, 0.35, 0.10), 0.9),
    "trunk":  mat("Stamm", (0.30, 0.20, 0.12), 0.9),
}

# ---------- primitives ----------
def box(name, sx, sy, sz, loc, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    if material:
        o.data.materials.append(material)
    return o

def cyl(name, r, depth, loc, material, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    if material:
        o.data.materials.append(material)
    return o

# wall along X at fixed y, with openings (cx, width, sill_z, top_z)
def wall_x(name, x0, x1, y, z0, h, t, openings=(), material=None, out=False):
    material = material or M["white"]
    openings = sorted(openings)
    parts = []
    cur = x0
    for (cx, w, sill, top) in openings:
        a, b = cx - w / 2, cx + w / 2
        if a > cur:
            parts.append((cur, a, z0, z0 + h))
        if sill > z0:
            parts.append((a, b, z0, sill))
        if top < z0 + h:
            parts.append((a, b, top, z0 + h))
        cur = b
    if cur < x1:
        parts.append((cur, x1, z0, z0 + h))
    objs = []
    for i, (a, b, za, zb) in enumerate(parts):
        if b - a > 0.001 and zb - za > 0.001:
            objs.append(box(f"{name}_{i}", b - a, t, zb - za,
                            ((a + b) / 2, y, (za + zb) / 2), material))
    return objs

# wall along Y at fixed x
def wall_y(name, y0, y1, x, z0, h, t, openings=(), material=None):
    material = material or M["white"]
    openings = sorted(openings)
    parts = []
    cur = y0
    for (cy, w, sill, top) in openings:
        a, b = cy - w / 2, cy + w / 2
        if a > cur:
            parts.append((cur, a, z0, z0 + h))
        if sill > z0:
            parts.append((a, b, z0, sill))
        if top < z0 + h:
            parts.append((a, b, top, z0 + h))
        cur = b
    if cur < y1:
        parts.append((cur, y1, z0, z0 + h))
    objs = []
    for i, (a, b, za, zb) in enumerate(parts):
        if b - a > 0.001 and zb - za > 0.001:
            objs.append(box(f"{name}_{i}", t, b - a, zb - za,
                            (x, (a + b) / 2, (za + zb) / 2), material))
    return objs

def window(name, cx, cy, w, h, z_sill, axis="x", frame=M["frame"]):
    ft = 0.06
    if axis == "x":
        box(f"{name}_glass", w - 0.08, 0.02, h - 0.08, (cx, cy, z_sill + h / 2), M["glass"])
        box(f"{name}_f_b", w, 0.10, ft, (cx, cy, z_sill + ft / 2), frame)
        box(f"{name}_f_t", w, 0.10, ft, (cx, cy, z_sill + h - ft / 2), frame)
        box(f"{name}_f_l", ft, 0.10, h, (cx - w / 2 + ft / 2, cy, z_sill + h / 2), frame)
        box(f"{name}_f_r", ft, 0.10, h, (cx + w / 2 - ft / 2, cy, z_sill + h / 2), frame)
        box(f"{name}_m", 0.05, 0.08, h, (cx, cy, z_sill + h / 2), frame)
    else:
        box(f"{name}_glass", 0.02, w - 0.08, h - 0.08, (cx, cy, z_sill + h / 2), M["glass"])
        box(f"{name}_f_b", 0.10, w, ft, (cx, cy, z_sill + ft / 2), frame)
        box(f"{name}_f_t", 0.10, w, ft, (cx, cy, z_sill + h - ft / 2), frame)
        box(f"{name}_f_l", 0.10, ft, h, (cx, cy - w / 2 + ft / 2, z_sill + h / 2), frame)
        box(f"{name}_f_r", 0.10, ft, h, (cx, cy + w / 2 - ft / 2, z_sill + h / 2), frame)
        box(f"{name}_m", 0.08, 0.05, h, (cx, cy, z_sill + h / 2), frame)

def door_panel(name, cx, cy, w, h, z0, axis="x", material=None, glass=False):
    material = material or M["door"]
    t = 0.05
    if axis == "x":
        box(name, w - 0.04, t, h - 0.04, (cx, cy, z0 + h / 2), material)
    else:
        box(name, t, w - 0.04, h - 0.04, (cx, cy, z0 + h / 2), material)

GF_H = 2.8      # ground floor wall height
UF_H = 2.6      # upper floor wall height
GF_Z0 = 0.0
UF_Z0 = 2.9     # upper floor finished floor level
T = 0.30        # exterior wall thickness
TI = 0.12       # interior wall thickness
HX, HY = 6.0, 4.5   # half extents of main house

# ---------- site ----------
box("Grundstück", 60, 60, 0.2, (0, 0, -0.1), M["grass"])

# ---------- ground floor slab & ceilings ----------
box("Bodenplatte_EG", 2 * HX, 2 * HY, 0.25, (0, 0, -0.125), M["concrete"])
# EG-Decke mit Treppenöffnung (x 1.25..2.45, y -3.7..1.0)
box("Decke_EG_A", 7.25, 2 * HY, 0.10, (-2.375, 0, GF_H + 0.05), M["ceiling"])
box("Decke_EG_B", 3.55, 2 * HY, 0.10, (4.225, 0, GF_H + 0.05), M["ceiling"])
box("Decke_EG_C", 1.2, 0.8, 0.10, (1.85, -4.1, GF_H + 0.05), M["ceiling"])
box("Decke_EG_D", 1.2, 3.5, 0.10, (1.85, 2.75, GF_H + 0.05), M["ceiling"])
box("Decke_OG", 2 * HX, 2 * HY, 0.10, (0, 0, UF_Z0 + UF_H + 0.05), M["ceiling"])

# ---------- ground floor exterior walls ----------
# front (y=-4.5): door at x=1.0, windows living/WC
wall_x("EG_Front", -HX, HX, -HY, GF_Z0, GF_H, T, openings=[
    (1.0, 1.1, 0.0, 2.1),      # Haustür
    (-3.5, 2.0, 0.8, 2.4),     # Wohnzimmer
    (4.2, 1.0, 1.2, 2.3),      # Gäste-WC
], material=M["beige"])
window("EG_Front_Wohnen", -3.5, -HY, 2.0, 1.6, 0.8)
window("EG_Front_WC", 4.2, -HY, 1.0, 1.1, 1.2)
def open_door(name, hinge, angle_deg):
    d = bpy.data.objects[name]
    h = bpy.data.objects.new(name + "_Scharnier", None)
    bpy.context.collection.objects.link(h)
    h.location = hinge
    d.parent = h
    h.rotation_euler.z = math.radians(angle_deg)

door_panel("Haustür", 1.0, -HY, 1.1, 2.1, 0.0)
open_door("Haustür", (0.45, -HY, 0.0), 60)
cyl("Türklinke", 0.03, 0.12, (1.45, -HY - 0.06, 1.05), M["frame"], rot=(math.pi / 2, 0, 0))
bpy.data.objects["Türklinke"].parent = bpy.data.objects["Haustür_Scharnier"]

# back (y=+4.5): dining window + kitchen glass sliding door
wall_x("EG_Hinten", -HX, HX, HY, GF_Z0, GF_H, T, openings=[
    (-3.5, 1.8, 0.8, 2.4),
    (2.5, 2.4, 0.0, 2.3),      # Küchenglastür
], material=M["beige"])
window("EG_Hinten_Essen", -3.5, HY, 1.8, 1.6, 0.8)
# glass sliding door (two panes)
box("Küchenglastür_1", 1.16, 0.04, 2.26, (1.91, HY, 1.15), M["glass"])
box("Küchenglastür_2", 1.16, 0.04, 2.26, (3.09, HY, 1.15), M["glass"])
box("Küchenglastür_Rahmen_u", 2.4, 0.10, 0.06, (2.5, HY, 0.03), M["frame"])
box("Küchenglastür_Rahmen_o", 2.4, 0.10, 0.06, (2.5, HY, 2.27), M["frame"])

# west (x=-6): living + dining
wall_y("EG_West", -HY, HY, -HX, GF_Z0, GF_H, T, openings=[
    (-1.5, 2.0, 0.8, 2.4),
    (2.5, 1.8, 0.8, 2.4),
], material=M["beige"])
window("EG_West_Wohnen", -HX, -1.5, 2.0, 1.6, 0.8, axis="y")
window("EG_West_Essen", -HX, 2.5, 1.8, 1.6, 0.8, axis="y")

# east (x=+6): kitchen + WC
wall_y("EG_Ost", -HY, HY, HX, GF_Z0, GF_H, T, openings=[
    (2.6, 1.5, 0.8, 2.4),
    (-2.8, 0.8, 1.2, 2.3),
], material=M["beige"])
window("EG_Ost_Küche", HX, 2.6, 1.5, 1.6, 0.8, axis="y")
window("EG_Ost_WC", HX, -2.8, 0.8, 1.1, 1.2, axis="y")

# ---------- ground floor interior walls ----------
wall_x("EG_Trenn_Süd", -HX + T, 2.5, 1.0, GF_Z0, GF_H, TI, openings=[
    (-3.1, 1.2, 0.0, 2.1),     # Wohnen -> Essen
    (0.5, 1.0, 0.0, 2.1),      # Halle -> Küche
])
wall_y("EG_Trenn_West", -HY + T, 1.0, -0.5, GF_Z0, GF_H, TI, openings=[
    (-1.5, 1.4, 0.0, 2.1),     # Wohnen -> Halle
])
wall_y("EG_Trenn_WC", -HY + T, 1.0, 2.5, GF_Z0, GF_H, TI, openings=[
    (-3.0, 0.9, 0.0, 2.1),     # Halle -> WC
])
# garage door in east wall
wall_y("EG_Ost_Garagetür", -4.2, -1.8, HX, GF_Z0, GF_H, T, openings=[(-3.0, 0.9, 0.0, 2.1)])
door_panel("Innentür_Garage", HX, -3.0, 0.9, 2.1, 0.0, axis="y", material=M["white"])

# ---------- stairs (entrance hall) ----------
n_steps = 16
run = 0.30
for i in range(n_steps):
    box(f"Treppe_{i}", 1.1, run + 0.02, 0.05,
        (1.85, -3.7 + i * run, (i + 1) * (UF_Z0 / n_steps) - 0.025), M["floor_w"])

# ---------- upper floor exterior walls (wood cladding) ----------
wall_x("OG_Front", -HX, HX, -HY, UF_Z0, UF_H, T, openings=[
    (-3.5, 1.4, UF_Z0 + 0.8, UF_Z0 + 2.2),
    (3.5, 1.4, UF_Z0 + 0.8, UF_Z0 + 2.2),
], material=M["wood"])
window("OG_Front_SZ2", -3.5, -HY, 1.4, 1.4, UF_Z0 + 0.8)
window("OG_Front_SZ3", 3.5, -HY, 1.4, 1.4, UF_Z0 + 0.8)

wall_x("OG_Hinten", -HX, HX, HY, UF_Z0, UF_H, T, openings=[
    (-3.5, 1.4, UF_Z0 + 0.8, UF_Z0 + 2.2),
    (3.5, 1.0, UF_Z0 + 0.8, UF_Z0 + 2.2),
], material=M["wood"])
window("OG_Hinten_SZ1", -3.5, HY, 1.4, 1.4, UF_Z0 + 0.8)
window("OG_Hinten_Bad", 3.5, HY, 1.0, 1.4, UF_Z0 + 0.8)

wall_y("OG_West", -HY, HY, -HX, UF_Z0, UF_H, T, openings=[
    (2.5, 1.4, UF_Z0 + 0.8, UF_Z0 + 2.2),
    (-1.5, 1.4, UF_Z0 + 0.8, UF_Z0 + 2.2),
], material=M["wood"])
window("OG_West_SZ1", -HX, 2.5, 1.4, 1.4, UF_Z0 + 0.8, axis="y")
window("OG_West_SZ2", -HX, -1.5, 1.4, 1.4, UF_Z0 + 0.8, axis="y")

wall_y("OG_Ost", -HY, HY, HX, UF_Z0, UF_H, T, openings=[
    (-2.0, 1.4, UF_Z0 + 0.8, UF_Z0 + 2.2),
    (1.0, 1.0, UF_Z0 + 0.8, UF_Z0 + 2.2),
], material=M["wood"])
window("OG_Ost_SZ3", HX, -2.0, 1.4, 1.4, UF_Z0 + 0.8, axis="y")
window("OG_Ost_Bad", HX, 1.0, 1.0, 1.4, UF_Z0 + 0.8, axis="y")

# ---------- upper floor interior walls ----------
wall_y("OG_Flur_West", -HY + T, HY - T, -0.5, UF_Z0, UF_H, TI, openings=[
    (2.0, 0.9, UF_Z0, UF_Z0 + 2.1),    # SZ1
    (-2.0, 0.9, UF_Z0, UF_Z0 + 2.1),   # SZ2
])
wall_y("OG_Flur_Ost", -HY + T, HY - T, 1.5, UF_Z0, UF_H, TI, openings=[
    (-2.0, 0.9, UF_Z0, UF_Z0 + 2.1),   # SZ3
    (1.0, 0.9, UF_Z0, UF_Z0 + 2.1),    # Bad
])
wall_x("OG_SZ1_Bad", -HX + T, -0.5, 2.2, UF_Z0, UF_H, TI, openings=[(-4.5, 0.8, UF_Z0, UF_Z0 + 2.1)])
wall_x("OG_Bad_Büro", 1.5, HX - T, 2.0, UF_Z0, UF_H, TI, openings=[(3.5, 0.8, UF_Z0, UF_Z0 + 2.1)])

# interior doors
for nm, x, y, ax in [("Tür_SZ1", -0.5, 2.0, "y"), ("Tür_SZ2", -0.5, -2.0, "y"),
                     ("Tür_SZ3", 1.5, -2.0, "y"), ("Tür_Bad", 1.5, 1.0, "y"),
                     ("Tür_SZ1_Bad", -4.5, 2.2, "x"), ("Tür_Büro", 3.5, 2.0, "x")]:
    if ax == "y":
        door_panel(nm, x, y, 0.9, 2.1, UF_Z0, axis="y", material=M["white"])
    else:
        door_panel(nm, x, y, 0.8, 2.1, UF_Z0, axis="x", material=M["white"])
open_door("Tür_SZ1", (-0.5, 1.55, UF_Z0), 75)
open_door("Tür_SZ2", (-0.5, -1.55, UF_Z0), -75)
open_door("Tür_Bad", (1.5, 0.55, UF_Z0), -75)
open_door("Tür_SZ3", (1.5, -1.55, UF_Z0), 75)

# ---------- floors ----------
box("Boden_EG", 2 * HX - 2 * T, 2 * HY - 2 * T, 0.04, (0, 0, 0.02), M["floor_w"])
box("Boden_OG_A", 6.95, 8.4, 0.04, (-2.225, 0, UF_Z0 + 0.02), M["floor_w"])
box("Boden_OG_B", 3.25, 8.4, 0.04, (4.075, 0, UF_Z0 + 0.02), M["floor_w"])
box("Boden_OG_C", 1.2, 0.5, 0.04, (1.85, -3.95, UF_Z0 + 0.02), M["floor_w"])
box("Boden_OG_D", 1.2, 3.2, 0.04, (1.85, 2.6, UF_Z0 + 0.02), M["floor_w"])
box("Boden_WC", 3.2, 2.7, 0.045, (4.1, -2.85, 0.025), M["floor_t"])
box("Boden_Küche", 5.7, 3.2, 0.045, (2.85, 2.6, 0.025), M["floor_t"])
box("Boden_Bad_OG", 4.2, 2.0, 0.045, (3.6, 1.0, UF_Z0 + 0.025), M["floor_t"])

# ---------- roof ----------
pitch = math.radians(30)
half_d = HY + 0.4
rise = half_d * math.tan(pitch)
ridge_z = UF_Z0 + UF_H + rise
slope_len = math.sqrt(half_d ** 2 + rise ** 2)
ang = math.atan2(rise, half_d)
for s in (-1, 1):
    box(f"Dachfläche_{'hinten' if s > 0 else 'vorn'}", 2 * HX + 0.8, slope_len, 0.12,
        (0, s * half_d / 2, UF_Z0 + UF_H + rise / 2),
        M["roof"], rot=(s * ang, 0, 0))
# gable walls (wood)
for s, nm in ((-1, "West"), (1, "Ost")):
    verts = [(-0.15, -HY - 0.15, 0), (0.15, -HY - 0.15, 0), (0.15, HY + 0.15, 0),
             (-0.15, HY + 0.15, 0), (-0.15, -HY - 0.15, rise), (0.15, -HY - 0.15, rise),
             (0.15, HY + 0.15, rise), (-0.15, HY + 0.15, rise)]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new(f"Giebel_{nm}")
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(f"Giebel_{nm}", me)
    bpy.context.collection.objects.link(o)
    o.location = (s * (HX - 0.15), 0, UF_Z0 + UF_H)
    o.data.materials.append(M["wood"])
# solar panels on front slope
for i in range(4):
    for j in range(2):
        y = -HY - 0.4 + 1.1 + j * 1.9
        z = UF_Z0 + UF_H + (HY + 0.4 - abs(y)) * math.tan(pitch) + 0.08
        box(f"Solar_{i}_{j}", 1.7, 0.05, 1.05, (-4.5 + i * 2.6, y, z), M["solar"], rot=(-ang, 0, 0))

# ---------- garage annex ----------
GX0, GX1 = HX, HX + 6.0
GY0, GY1 = -HY, 2.0
GZ = 2.8
box("Garage_Boden", GX1 - GX0, GY1 - GY0, 0.15, ((GX0 + GX1) / 2, (GY0 + GY1) / 2, 0.075), M["concrete"])
wall_x("Garage_Front", GX0, GX1, GY0, 0, GZ, T, openings=[(GX0 + 3.0, 2.6, 0.0, 2.3)], material=M["beige"])
box("Garagentor", 2.6, 0.06, 2.3, (GX0 + 3.0, GY0, 1.15), M["garage"])
for i in range(1, 5):
    box(f"Garagentor_Fuge_{i}", 2.6, 0.02, 0.02, (GX0 + 3.0, GY0 - 0.035, i * 0.46), M["frame"])
wall_y("Garage_West", GY0, GY1, GX0, 0, GZ, T, material=M["beige"])  # shared wall
wall_y("Garage_Ost", GY0, GY1, GX1, 0, GZ, T, material=M["beige"])
wall_x("Garage_Hinten", GX0, GX1, GY1, 0, GZ, T, material=M["beige"])
box("Garage_Dach", GX1 - GX0 + 0.4, GY1 - GY0 + 0.4, 0.15, ((GX0 + GX1) / 2, (GY0 + GY1) / 2, GZ + 0.075), M["roof"])
# car
cb = (GX0 + 3.0, -1.2)
box("Auto_Karosserie", 1.8, 4.2, 0.7, (cb[0], cb[1], 0.85), M["car"])
box("Auto_Kabine", 1.6, 2.0, 0.55, (cb[0], cb[1] - 0.2, 1.45), M["car"])
for wx in (-0.85, 0.85):
    for wy in (-1.35, 1.35):
        cyl(f"Auto_Rad_{wx}_{wy}", 0.33, 0.25, (cb[0] + wx, cb[1] + wy, 0.33), M["tire"], rot=(0, math.pi / 2, 0))

# ---------- terrace ----------
box("Terrasse", 8.0, 3.5, 0.14, (-2.0, HY + 1.75, 0.07), M["concrete"])
box("Gartentisch", 1.8, 0.9, 0.06, (-2.0, HY + 1.6, 0.78), M["table"])
for lx in (-0.7, 0.7):
    cyl("Gartentisch_Bein", 0.05, 0.72, (-2.0 + lx, HY + 1.6, 0.36), M["table"])
for i, (cx, cy) in enumerate([(-3.2, HY + 1.0), (-3.2, HY + 2.2), (-0.8, HY + 1.0), (-0.8, HY + 2.2)]):
    box(f"Terrassenstuhl_{i}", 0.45, 0.45, 0.08, (cx, cy, 0.62), M["sofa"])
    box(f"Terrassenstuhl_Rücken_{i}", 0.45, 0.08, 0.5, (cx, cy + (0.2 if cy < HY + 1.6 else -0.2), 0.9), M["sofa"])

# trees
for tx, ty, s in ((-13, -9, 1.0), (16.5, -4, 0.8), (-15, 7, 1.2), (14, 10, 0.9)):
    cyl(f"Baumstamm_{tx}_{ty}", 0.25 * s, 3.0 * s, (tx, ty, 1.5 * s), M["trunk"])
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.6 * s, location=(tx, ty, 3.6 * s))
    o = bpy.context.active_object
    o.name = f"Baumkrone_{tx}_{ty}"
    o.data.materials.append(M["leaf"])

# ---------- furniture ground floor ----------
# living room
box("Sofa_Sitz", 2.4, 0.95, 0.45, (-3.2, -3.4, 0.42), M["sofa"])
box("Sofa_Rücken", 2.4, 0.25, 0.55, (-3.2, -3.85, 0.85), M["sofa"])
box("Sofa_Arm_L", 0.25, 0.95, 0.62, (-4.45, -3.4, 0.5), M["sofa"])
box("Sofa_Arm_R", 0.25, 0.95, 0.62, (-1.95, -3.4, 0.5), M["sofa"])
box("Couchtisch", 1.1, 0.6, 0.08, (-3.2, -2.2, 0.52), M["table"])
box("TV_Board", 1.8, 0.4, 0.5, (-3.2, -0.2, 0.25), M["worktop"])
box("TV", 1.4, 0.06, 0.8, (-3.2, -0.2, 1.15), M["frame"])
box("Sessel_Sitz", 0.9, 0.9, 0.45, (-1.6, -1.2, 0.42), M["sofa"])
box("Sessel_Rücken", 0.9, 0.22, 0.55, (-1.6, -1.65, 0.85), M["sofa"])
# dining
box("Esstisch", 1.0, 2.0, 0.06, (-3.5, 2.6, 0.78), M["table"])
for lx in (-0.35, 0.35):
    box(f"Esstisch_Bein_{lx}", 0.08, 0.08, 0.75, (-3.5 + lx, 2.6, 0.375), M["table"])
for i, (cx, cy) in enumerate([(-4.4, 2.0), (-4.4, 3.2), (-2.6, 2.0), (-2.6, 3.2), (-3.5, 1.6), (-3.5, 3.6)]):
    box(f"Stuhl_{i}", 0.42, 0.42, 0.06, (cx, cy, 0.55), M["wood"])
    box(f"Stuhl_Rücken_{i}", 0.42, 0.06, 0.5, (cx, cy + (0.18 if cy < 2.6 else -0.18), 0.85), M["wood"])
# kitchen L-counter
box("Küche_Zeile_A", 5.2, 0.65, 0.9, (2.9, 3.85, 0.45), M["counter"])
box("Küche_Zeile_B", 0.65, 2.6, 0.9, (5.35, 2.3, 0.45), M["counter"])
box("Küche_Platte_A", 5.2, 0.7, 0.05, (2.9, 3.85, 0.925), M["worktop"])
box("Küche_Platte_B", 0.7, 2.6, 0.05, (5.35, 2.3, 0.925), M["worktop"])
box("Küche_Oberschränke_A", 3.0, 0.35, 0.7, (3.5, 4.25, 1.85), M["counter"])
box("Kühlschrank", 0.7, 0.7, 1.9, (0.1, 4.1, 0.95), M["fixture"])
box("Herd", 0.6, 0.5, 0.02, (4.2, 3.85, 0.96), M["frame"])
cyl("Spüle", 0.25, 0.02, (2.2, 3.85, 0.965), M["fixture"])
cyl("Armatur", 0.02, 0.35, (2.2, 4.1, 1.12), M["frame"])
# guests WC
box("WC_Schüssel", 0.4, 0.55, 0.42, (4.9, -3.9, 0.21), M["fixture"])
box("WC_Spülkasten", 0.45, 0.15, 0.5, (4.9, -4.1, 0.65), M["fixture"])
cyl("WC_Waschbecken", 0.25, 0.15, (4.0, -3.9, 0.85), M["fixture"])

# ---------- furniture upper floor ----------
def bed(nm, x, y, w=1.8, l=2.1):
    box(f"{nm}_Rahmen", w, l, 0.3, (x, y, UF_Z0 + 0.25), M["table"])
    box(f"{nm}_Matratze", w - 0.1, l - 0.1, 0.22, (x, y, UF_Z0 + 0.51), M["bed"])
    box(f"{nm}_Decke", w - 0.1, l * 0.6, 0.12, (x, y - 0.25, UF_Z0 + 0.68), M["bed2"])
    box(f"{nm}_Kissen", w - 0.3, 0.4, 0.12, (x, y + l / 2 - 0.4, UF_Z0 + 0.68), M["bed"])
    box(f"{nm}_Kopfteil", w, 0.08, 0.9, (x, y + l / 2 + 0.06, UF_Z0 + 0.55), M["table"])

bed("Bett_SZ1", -3.2, 3.0)
bed("Bett_SZ2", -3.2, -2.0, w=1.6, l=2.0)
bed("Bett_SZ3", 3.6, -2.0, w=1.4, l=2.0)
for nm, x, y, ry in [("Schrank_SZ1", -5.2, 1.2, 0), ("Schrank_SZ2", -5.2, -3.5, 0),
                     ("Schrank_SZ3", 5.2, -3.5, 0)]:
    box(nm, 0.6, 2.0, 2.2, (x, y, UF_Z0 + 1.1), M["wood"])
# family bath
box("Badewanne", 1.7, 0.75, 0.55, (5.0, 0.6, UF_Z0 + 0.275), M["fixture"])
box("Dusche_Boden", 0.9, 0.9, 0.02, (2.3, 1.4, UF_Z0 + 0.03), M["floor_t"])
box("Dusche_Wand", 0.9, 0.02, 2.0, (2.3, 0.96, UF_Z0 + 1.0), M["glass"])
box("Dusche_Wand2", 0.02, 0.9, 2.0, (1.86, 1.4, UF_Z0 + 1.0), M["glass"])
box("Waschtisch_OG", 0.9, 0.5, 0.1, (2.6, 0.35, UF_Z0 + 0.85), M["fixture"])
box("WC_OG", 0.4, 0.55, 0.42, (4.2, 1.6, UF_Z0 + 0.21), M["fixture"])
# en-suite SZ1
box("Dusche_SZ1", 0.85, 0.85, 0.02, (-5.1, 3.6, UF_Z0 + 0.03), M["floor_t"])
box("WC_SZ1", 0.4, 0.55, 0.42, (-3.6, 3.8, UF_Z0 + 0.21), M["fixture"])
box("Waschtisch_SZ1", 0.8, 0.45, 0.1, (-5.1, 2.7, UF_Z0 + 0.85), M["fixture"])

# ---------- lights ----------
def sun():
    l = bpy.data.lights.new("Sonne", 'SUN')
    l.energy = 3.5
    l.angle = math.radians(5)
    o = bpy.data.objects.new("Sonne", l)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = (math.radians(50), 0, math.radians(-35))
sun()

def room_light(name, x, y, z, energy=60):
    l = bpy.data.lights.new(name, 'POINT')
    l.energy = energy
    l.shadow_soft_size = 0.3
    o = bpy.data.objects.new(name, l)
    bpy.context.collection.objects.link(o)
    o.location = (x, y, z)

room_light("L_Wohnen", -3.2, -2.0, 2.4, 90)
room_light("L_Essen", -3.5, 2.6, 2.4, 70)
room_light("L_Küche", 2.5, 2.5, 2.4, 80)
room_light("L_Halle", 1.0, -2.5, 2.4, 60)
room_light("L_WC", 4.2, -2.8, 2.3, 30)
room_light("L_Garage", 9.0, -1.0, 2.5, 50)
room_light("L_Flur", 0.5, 0.0, UF_Z0 + 2.3, 60)
room_light("L_SZ1", -3.2, 2.2, UF_Z0 + 2.3, 60)
room_light("L_SZ2", -3.2, -2.0, UF_Z0 + 2.3, 60)
room_light("L_SZ3", 3.6, -2.0, UF_Z0 + 2.3, 60)
room_light("L_Bad", 3.5, 1.0, UF_Z0 + 2.3, 50)
room_light("L_Büro", 3.5, 3.2, UF_Z0 + 2.3, 50)

world = bpy.data.worlds.new("Welt")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.75, 0.82, 0.92, 1.0)
bg.inputs[1].default_value = 0.6

# ---------- camera tour ----------
def key(obj, frame, loc):
    obj.location = loc
    obj.keyframe_insert(data_path="location", frame=frame)

fps = 24
cam_data = bpy.data.cameras.new("TourCam")
cam_data.lens = 20
cam = bpy.data.objects.new("TourCam", cam_data)
bpy.context.collection.objects.link(cam)
target = bpy.data.objects.new("CamTarget", None)
bpy.context.collection.objects.link(target)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

UF_MID = UF_Z0 + 1.4
path = [
    # (frame, cam pos, look target)
    (0,    (9.0, -14.0, 2.2),  (0, 0, 3.0)),            # Establishing: total view
    (48,   (2.0, -10.0, 1.8),  (1.0, -4.5, 1.5)),       # approach front door
    (80,   (1.0, -2.8, 1.5),   (-3.0, -1.5, 1.2)),      # entrance hall
    (96,   (-0.5, -1.5, 1.5),  (-5.0, -1.0, 1.2)),      # through opening into living room
    (118,  (-3.0, -1.8, 1.5),  (-5.5, 0.5, 1.2)),       # living room
    (148,  (-3.4, 1.8, 1.5),   (-3.5, 4.0, 1.2)),       # dining room
    (178,  (-0.5, 2.6, 1.5),   (3.0, 3.5, 1.2)),        # kitchen with glass door
    (208,  (1.0, -0.5, 1.5),   (1.9, -3.5, 1.8)),       # back to hall, stairs in view
    (240,  (1.85, -1.0, 2.3),  (1.9, 1.5, 3.6)),        # climbing the stairs
    (272,  (0.5, 0.5, UF_MID), (-3.0, 2.5, UF_MID)),    # upstairs hallway -> SZ1
    (286,  (-0.5, 2.0, UF_MID), (-4.0, 3.0, UF_MID)),   # through SZ1 door
    (306,  (-3.2, 1.8, UF_MID), (-5.0, 3.5, UF_MID)),   # master bedroom + en-suite
    (320,  (-0.5, 2.0, UF_MID), (0.0, 0.0, UF_MID)),    # back through door
    (327,  (0.3, 0.0, UF_MID),  (-3.5, -2.5, UF_MID)),  # hallway
    (334,  (-0.5, -2.0, UF_MID), (-3.5, -2.5, UF_MID)), # through SZ2 door
    (348,  (0.3, -1.0, UF_MID), (4.0, 1.0, UF_MID)),    # hallway toward east
    (360,  (0.8, 0.2, UF_MID),  (4.5, 1.0, UF_MID)),    # approach bath
    (372,  (1.5, 1.0, UF_MID),  (4.5, 1.0, UF_MID)),    # bath door
    (384,  (1.2, -0.5, UF_MID), (1.5, -2.0, UF_MID)),   # turn to SZ3
    (396,  (1.5, -2.0, UF_MID), (3.6, -2.5, UF_MID)),   # SZ3 door
    (412,  (2.6, -2.2, UF_MID), (3.6, -4.4, UF_MID)),   # SZ3 + window view
    (440,  (2.6, -2.2, UF_MID), (3.6, -4.4, UF_MID)),
]
for f, p, t in path:
    key(cam, f, p)
    key(target, f, t)

scene.render.fps = fps
scene.frame_start = 0
scene.frame_end = 440
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 3
scene.cycles.transmission_bounces = 6
scene.cycles.transparent_max_bounces = 4
scene.render.use_persistent_data = True
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = "/workspace/output/frames/"

# ---------- save & export ----------
bpy.ops.wm.save_as_mainfile(filepath="/workspace/output/familienhaus.blend")
bpy.ops.export_scene.gltf(filepath="/workspace/output/familienhaus.glb", export_format='GLB', use_selection=False)
print("BUILD_OK")
