# Familienhaus 3D – Blender-Modell & Room-Tour

3D-Modell eines zweistöckigen Familienhauses (Satteldach, Garage mit Flachdach,
Terrasse), erstellt in Blender 5.0 anhand von Fassadenbild und Grundriss.

## Inhalte

| Datei | Beschreibung |
|---|---|
| `modell/familienhaus.blend` | natives Blender-File (Blender 5.0), direkt öffnen |
| `modell/familienhaus.glb` | glTF-Export für Blender, Sketchfab, Unity, Godot, Windows-3D-Viewer etc. |
| `video/roomtour.mp4` | Room-Tour-Video (~18 s, 960×540, 24 fps, H.264) – Kamerafahrt durch alle Räume |
| `renders/` | Vorschau-Renderings (Außen + Innen) |
| `house_build.py` | vollständiges Build-Skript (Modell per Skript reproduzierbar) |

## Grundriss

**Erdgeschoss:** Eingangsdiele mit Treppe · Wohnzimmer · Esszimmer · Küche mit
Küchenglastür · Gäste-WC · Garage ( angebaut, Flachdach, mit Auto)

**Obergeschoss:** 3 Schlafzimmer (SZ1 mit eigenem Bad) · Familienbad mit Wanne
und Dusche · Büro · Flur

**Außen:** Satteldach mit Solarpanels · EG beige, OG + Giebel in Holzbraun ·
Terrasse mit Sitzgruppe · Grundstück mit Bäumen

## Modell wiederherstellen / anpassen

```bash
pip install bpy          # Blender als Python-Modul (Python 3.11)
python house_build.py    # baut das komplette Haus neu und exportiert .blend + .glb
```
