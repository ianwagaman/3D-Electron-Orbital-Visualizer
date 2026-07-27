import settings_manager, quantum_math, aesthetics
import random
import time
import os
import sys
import numpy as np
from vispy import scene
from vispy.io import imread

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def create_icon(filepath, hex_color, parent, pos=(0, 0), size=16):
    """Loads a PNG, preserves transparency, and generates a white and a colored array."""
    try:
        img = imread(filepath)
        # Ensure RGBA to preserve transparency
        if img.shape[2] == 3:
            img = np.dstack((img, np.full(img.shape[:2], 255, dtype=np.uint8)))

        # Create a purely white version (keeping original alpha)
        white_img = img.copy()
        white_img[..., :3] = 255

        # Create the colored version matching your UI layout
        h = hex_color.lstrip('#')
        rgb = [int(h[i:i+2], 16) for i in (0, 2, 4)]
        color_img = img.copy()
        for c in range(3):
            color_img[..., c] = rgb[c]

        # Scale down to fit the UI
        scale_x = size / img.shape[1]
        scale_y = size / img.shape[0]

        img_vis = scene.visuals.Image(white_img, parent=parent, interpolation='bicubic')
        img_vis.transform = scene.transforms.STTransform(scale=(scale_x, scale_y), translate=pos)

        return img_vis, white_img, color_img
    except Exception as e:
        print(f"Notice: Icon '{filepath}' not found or could not be loaded. Skipping.")
        return None, None, None

def setup_ui(app):
    was_frozen = getattr(app, '_frozen', False)
    if was_frozen and hasattr(app, 'unfreeze'):
        app.unfreeze()

    app.current_preset_slot = None
    app.preset_play_active = False
    app.preset_last_play_time = 0.0

    if was_frozen and hasattr(app, 'freeze'):
        app.freeze()

    app.ui_bg = scene.visuals.Rectangle(center=(130, app.size[1] / 2), width=320, height=app.size[1],
                                        color=(0.05, 0.05, 0.08, 0.9), border_color=(1, 1, 1, 1), border_width=1,
                                        parent=app.ui_container)
    app.hamburger = scene.visuals.Text("=", pos=(20, 25), color='white', font_size=24, bold=True, parent=app.scene)
    app.ui_elements["hamburger_y_pos"] = 25

    app.ui_elements.update({
        "help_btn": scene.visuals.Text("HELP", pos=(250, 25), color='#00aaff', font_size=10, bold=True,
                                       parent=app.scene),
        "help_icon": scene.visuals.Text("H", pos=(65, 25), color='#00aaff', font_size=14, bold=True, parent=app.scene),
        "help_y_pos": 25})

    for i, sid in enumerate(["basis", "n", "l", "m"]):
        y = 60 + i * 35
        app.ui_elements.update({
            f"{sid}_down": scene.visuals.Text("<", pos=(50, y), color='white', font_size=16, bold=True,
                                              parent=app.scene),
            f"{sid}_val": scene.visuals.Text(f"{sid}: ...", pos=(130, y), color='white', font_size=12,
                                             parent=app.scene),
            f"{sid}_up": scene.visuals.Text(">", pos=(210, y), color='white', font_size=16, bold=True,
                                            parent=app.scene),
            f"{sid}_y_pos": y})

    toggles = [("points", "Probability Cloud", "#ff007f"), ("surfaces", "Orbital Isosurface", "#ff0000"),
               ("nodes", "Nodal Boundary", "#ffff00"), ("axes", "Coordinate Axes", "#008000"),
               ("rotate", "Rotate", "#0000ff"), ("slice_x", "Slice X-Axis", "#800080"),
               ("slice_y", "Slice Y-Axis", "#800080"), ("slice_z", "Slice Z-Axis", "#800080")]

    y = 0
    for i, (tid, label, color) in enumerate(toggles):
        y = (60 + 3 * 35) + 50 + i * 40
        box = scene.visuals.Rectangle(center=(40, y), width=16, height=16, color=(0.05, 0.05, 0.08, 0.9),
                                      border_color=color, parent=app.scene)
        fill = scene.visuals.Rectangle(center=(40, y), width=10, height=10, color=color, parent=app.scene)
        lbl = scene.visuals.Text(label, pos=(65, y), color='white', anchor_x='left', font_size=11, parent=app.scene)

        app.ui_elements[tid] = {'box': box, 'fill': fill, 'lbl': lbl, 'y_pos': y, 'color': color}

        icon_path = resource_path(f"icons/{tid}_icon.png")
        if os.path.exists(icon_path):
            img_vis, white_img, color_img = create_icon(icon_path, color, app.scene, pos=(28, y - 12), size=24)
            if img_vis:
                app.ui_elements[tid].update({
                    'img_vis': img_vis,
                    'white_array': white_img,
                    'color_array': color_img})

    lbl_sets = {'color': 'white', 'font_size': 75, 'bold': True, 'anchor_x': 'center', 'anchor_y': 'center'}
    app.axis_labels = {'x': scene.visuals.Text('X', pos=(2, 0, 0), parent=app.view.scene, **lbl_sets),
                       'y': scene.visuals.Text('Y', pos=(0, 2, 0), parent=app.view.scene, **lbl_sets),
                       'z': scene.visuals.Text('Z', pos=(0, 0, 2), parent=app.view.scene, **lbl_sets)}
    for lbl in app.axis_labels.values(): lbl.visible = False

    rand_y = y + 40
    app.ui_elements.update({
        "random_bg": scene.visuals.Rectangle(center=(130, rand_y), width=160, height=30, color=(0.2, 0.1, 0.3, 0.9),
                                             border_color='#aa00ff', parent=app.scene),
        "random_lbl": scene.visuals.Text("RANDOMIZE", pos=(130, rand_y), color='#e0b0ff', font_size=9, bold=True,
                                         parent=app.scene),
        "random_y_pos": rand_y
    })

    app.ui_elements["random_icon"] = scene.visuals.Text("?", pos=(40, rand_y), color='#e0b0ff', font_size=12, bold=True, parent=app.scene)

    preset_start_y = rand_y + 60
    for i in range(1, 10):
        x_pos = 90 * ((i - 1) % 3) + 20
        y_pos = preset_start_y + ((i - 1) // 3) * 60 + (0 if (i - 1) % 3 == 1 else 30) - 15

        app.ui_elements[f"preset_{i}"] = {
            'box': scene.visuals.Rectangle(center=(x_pos, y_pos), width=16, height=16, color='#222',
                                           border_color='#555', parent=app.scene),
            'lbl': scene.visuals.Text(str(i), pos=(x_pos, y_pos), color='white', font_size=9, parent=app.scene),
            'state_lbl': scene.visuals.Text("...", pos=(x_pos + 12, y_pos), color='white', font_size=9, anchor_x='left',
                                            parent=app.scene),
            'y_pos': y_pos, 'x_pos': x_pos}

    play_x = 90 * 1 + 50
    play_y = preset_start_y + 4 * 40
    app.ui_elements["preset_play"] = {
        'box': scene.visuals.Rectangle(center=(play_x, play_y), width=16, height=16, color='#222', border_color='#555',
                                       parent=app.scene),
        'lbl': scene.visuals.Text(">", pos=(play_x, play_y), color='white', font_size=9, parent=app.scene),
        'y_pos': play_y, 'x_pos': play_x}

    app.min_elements = {
        'basis': scene.visuals.Text("R|", pos=(65, 25), color='white', font_size=14, bold=True, parent=app.scene),
        'n': scene.visuals.Text("1", pos=(95, 25), color='white', font_size=14, bold=True, parent=app.scene),
        'l': scene.visuals.Text("0", pos=(120, 25), color='white', font_size=14, bold=True, parent=app.scene),
        'm': scene.visuals.Text("0", pos=(145, 25), color='white', font_size=14, bold=True, parent=app.scene),
        'close': scene.visuals.Text(">", pos=(170, 25), color='white', font_size=14, bold=True, parent=app.scene),
        'name': scene.visuals.Text("1s", pos=(85, 65), color='white', font_size=14, bold=True, parent=app.scene)}

    bottom_y = preset_start_y + 190
    app.ui_elements.update({
        "color_btn": scene.visuals.Text("COLORS", pos=(50, bottom_y), color='#00ff00', font_size=8, bold=True,
                                        parent=app.scene),
        "bg_btn": scene.visuals.Text("ENVIRONMENT", pos=(200, bottom_y), color='#00aaff', font_size=8, bold=True,
                                     parent=app.scene),
        "color_med": scene.visuals.Text("C", pos=(20, bottom_y), color='#00ff00', font_size=12, bold=True,
                                        parent=app.scene),
        "bg_med": scene.visuals.Text("E", pos=(60, bottom_y), color='#00aaff', font_size=12, bold=True,
                                     parent=app.scene),
        "color_btn_y": bottom_y, "bg_btn_y": bottom_y})

    update_layout_mode(app)
    sync_ui(app)
    app.update()

def update_layout_mode(app):
    if app.ui_mode == "full":
        t_width = 290
        is_full, is_med, is_vis = True, False, True
    elif app.ui_mode == "medium":
        t_width = 90
        is_full, is_med, is_vis = False, True, True
    else:
        t_width = 0
        is_full, is_med, is_vis = False, False, False

    w, h = app.size

    safe_w = max(10, w - t_width)
    safe_h = max(10, h)

    if hasattr(app, 'bg_view'):
        app.bg_view.pos = (t_width, 0)
        app.bg_view.size = (safe_w, safe_h)

    if hasattr(app, 'view'):
        app.view.pos = (t_width, 0)
        app.view.size = (safe_w, safe_h)

    if hasattr(app, 'ui_bg'):
        app.ui_bg.visible = is_vis
        app.ui_bg.height = h
        if is_vis:
            app.ui_bg.width, app.ui_bg.center = (320, (130, h / 2)) if is_full else (90, (45, h / 2))

    for tid, els in app.ui_elements.items():
        if isinstance(els, dict):
            has_icon = 'img_vis' in els
            if 'lbl' in els and tid != 'preset_play': els['lbl'].visible = is_full
            if 'box' in els: els['box'].visible = is_full if has_icon else is_vis
            if 'fill' in els: els['fill'].visible = is_full if has_icon else is_vis
            if 'icon' in els: els['icon'].visible = is_med
            if 'state_lbl' in els: els['state_lbl'].visible = is_full
            if has_icon: els['img_vis'].visible = is_med

    app.ui_elements["color_btn"].visible = app.ui_elements["bg_btn"].visible = is_full
    if "color_med" in app.ui_elements: app.ui_elements["color_med"].visible = app.ui_elements["bg_med"].visible = is_med

    for i in range(1, 10):
        if f"preset_{i}" in app.ui_elements:
            p = app.ui_elements[f"preset_{i}"]
            p['state_lbl'].visible = is_full
            new_x = 10 + ((i - 1) % 3) * 30 if is_med else p['x_pos']
            p['box'].center, p['lbl'].pos, p['lbl'].visible = (new_x, p['y_pos']), (new_x, p['y_pos']), (
                    is_med or is_full)

    if "preset_play" in app.ui_elements:
        p = app.ui_elements["preset_play"]
        new_x = 40 if is_med else p['x_pos']
        p['box'].center, p['lbl'].pos = (new_x, p['y_pos']), (new_x, p['y_pos'])
        p['lbl'].visible = p['box'].visible = (is_med or is_full)

    for sid in ["basis", "n", "l", "m"]:
        for s in ["down", "val", "up"]: app.ui_elements[f"{sid}_{s}"].visible = is_vis
        dx, vx, ux = (50, 130, 210) if is_full else (15, 45, 75)
        if is_vis:
            y = app.ui_elements[f"{sid}_y_pos"]
            app.ui_elements[f"{sid}_down"].pos, app.ui_elements[f"{sid}_val"].pos, app.ui_elements[f"{sid}_up"].pos = (
                dx, y), (vx, y), (ux, y)

    app.ui_elements["random_bg"].visible = app.ui_elements["random_lbl"].visible = is_full
    app.ui_elements["random_icon"].visible = is_med
    app.hamburger.visible = True

    if "help_btn" in app.ui_elements:
        app.ui_elements["help_btn"].visible = is_full
        app.ui_elements["help_icon"].visible = is_med

    if hasattr(app, 'min_elements'):
        for vis in app.min_elements.values(): vis.visible = app.ui_mode == "hidden"

    sync_ui(app)

    if hasattr(app, 'bg_manager'):
        app.bg_manager.refresh_grid(t_width=t_width, w=w, h=h)

def get_orbital_name(n, l, m, basis):
    if basis == 'comp':
        l_char = ['s', 'p', 'd', 'f'][l] if l < 4 else str(l)
        return f"{n}{l_char} (m={m})"

    lookup_m = abs(m)

    if basis == 'imag' and m == 0:
        return "0 (Empty)"

    name = quantum_math.ORBITAL_NAMES.get((n, l, lookup_m, basis), "")

    if not name:
        l_char = ['s', 'p', 'd', 'f'][l] if l < 4 else str(l)
        name = f"{n}{l_char}"

    return name

def sync_ui(app):
    states = {"points": app.show_points, "surfaces": app.show_surfaces, "nodes": app.show_nodes, "axes": app.show_axes,
              "rotate": app.rotate, "slice_x": app.slice_x, "slice_y": app.slice_y, "slice_z": app.slice_z}

    for tid, els in app.ui_elements.items():
        if not isinstance(els, dict) or tid == "hamburger_y_pos": continue
        is_active = states.get(tid, True)

        if 'fill' in els:
            els['fill'].color = els.get('color', '#fff') if is_active else (0.05, 0.05, 0.08, 0.9)

        # --- NEW CODE FOR ICON TINTING ---
        if 'img_vis' in els:
            if is_active:
                els['img_vis'].set_data(els['color_array'])
            else:
                els['img_vis'].set_data(els['white_array'])

        if tid == "preset_play":
            is_active = getattr(app, 'preset_play_active', False)
            els['box'].border_color = '#00ffcc' if is_active else '#555'
            els['lbl'].color = '#00ffcc' if is_active else 'white'
            continue

        if 'lbl' in els and not tid.startswith("preset_"): els['lbl'].color = 'white'

        if tid.startswith("preset_") and tid != "preset_play":
            slot = tid.split("_")[1]
            is_pop = hasattr(app, 'presets') and slot in app.presets
            els['state_lbl'].visible = app.ui_mode == "full"
            els['box'].color = '#222'
            els['box'].border_color = '#00ffcc' if is_pop else '#555'

            els['lbl'].color = '#00ffcc' if is_pop else 'white'
            els['state_lbl'].color = '#00ffcc' if is_pop else 'white'

            if is_pop:
                st = app.presets[slot]
                els[
                    'state_lbl'].text = f"{ {'real': 'R', 'imag': 'I', 'comp': 'C'}.get(st['basis'], 'R')}|{st['n']}{st['l']}{st['m']}>"
            else:
                els['state_lbl'].text = "B|nlm>"

    for sid in ["n", "l", "m"]:
        app.ui_elements[
            f"{sid}_val"].text = f"{f'{sid} = ' if app.ui_mode == 'full' else ''}{app.input_buffer + '_' if app.active_input == sid else getattr(app, sid)}"
        app.ui_elements[f"{sid}_val"].color = 'white'

    app.ui_elements["basis_val"].text = {"real": "R", "imag": "I", "comp": "C"}.get(app.basis, app.basis[
        0].upper()) if app.ui_mode == "medium" else {"real": "Real", "imag": "Imaginary", "comp": "Complex"}.get(
        app.basis, app.basis.capitalize())
    app.ui_elements["l_down"].color = app.ui_elements["l_up"].color = 'white' if app.n > 1 else 'gray'
    app.ui_elements["m_down"].color = app.ui_elements["m_up"].color = 'white' if app.l > 0 else 'gray'

    if hasattr(app, 'min_elements'):
        app.min_elements['basis'].text = f"{ {'real': 'R', 'imag': 'I', 'comp': 'C'}.get(app.basis, 'R')}|"
        for sid in ['n', 'l', 'm']:
            app.min_elements[
                sid].text = f"{app.input_buffer if app.active_input == sid else str(getattr(app, sid))}{',' if sid != 'm' else ''}"
            app.min_elements[sid].color = 'white'

        app.min_elements['name'].text = get_orbital_name(app.n, app.l, app.m, app.basis)
    app.update()

def _check(app, event, key, tid):
    if getattr(event, 'key', None) and hasattr(event.key, 'name') and event.key.name.upper() == key: return True

    max_x = 200 if app.ui_mode == "full" else (90 if app.ui_mode == "medium" else 0)

    if getattr(event, 'button', None) == 1 and event.pos[0] < max_x:
        y_pos = -100
        if tid in app.ui_elements and isinstance(app.ui_elements[tid], dict):
            y_pos = app.ui_elements[tid].get('y_pos', -100)
        else:
            prefix = tid.split('_')[0]
            y_pos = app.ui_elements.get(f"{prefix}_y_pos", -100)

        return abs(event.pos[1] - y_pos) < 15
    return False

def point_cloud_toggle(app, event=None):
    if event:
        if not _check(app, event, 'P', 'points'): return False
        app.show_points = not app.show_points
        sync_ui(app)

    if hasattr(app, 'scatter_pos'):
        app.scatter_pos.visible = app.show_points
    if hasattr(app, 'scatter_neg'):
        app.scatter_neg.visible = app.show_points
    return True if event else None

def isosurface_toggle(app, event=None):
    if event:
        # Reduced to a single check for the 'S' hotkey to resolve the conflict
        if not _check(app, event, 'S', 'surfaces'): return False
        app.show_surfaces = not app.show_surfaces
        sync_ui(app)

    if hasattr(app, 'pos_meshes'):
        for mesh in app.pos_meshes: mesh.visible = app.show_surfaces
    if hasattr(app, 'neg_meshes'):
        for mesh in app.neg_meshes: mesh.visible = app.show_surfaces
    return True if event else None

def nodes_toggle(app, event=None):
    if event:
        if not _check(app, event, 'N', 'nodes'): return False
        app.show_nodes = not app.show_nodes
        sync_ui(app)

    if hasattr(app, 'node_visuals'):
        for node in app.node_visuals: node.visible = app.show_nodes
    return True if event else None

def axes_toggle(app, event=None):
    if event:
        if not _check(app, event, 'A', 'axes'): return False
        app.show_axes = not app.show_axes
        sync_ui(app)

    if hasattr(app, 'axes_visual'):
        app.axes_visual.visible = app.show_axes
        for label in app.axis_labels.values(): label.visible = app.show_axes
        if app.show_axes:
            length = 0.875*(app.n**2) + 7.775*app.n - 5.625
            app.axes_visual.transform = scene.transforms.MatrixTransform()
            app.axes_visual.transform.scale((length, length, length))
            app.axis_labels['x'].pos, app.axis_labels['y'].pos, app.axis_labels['z'].pos = (length * 1.2, 0, 0), (
                0, length * 1.2, 0), (0, 0, length * 1.2)
            for label in app.axis_labels.values():
                label.font_size = 60 * length
    return True if event else None

def preset_play_toggle(app, update=False, event=None):
    if event:
        triggered = False
        if getattr(event, 'key', None) and hasattr(event.key, 'name') and event.key.name.upper() == 'SPACE':
            triggered = True
        elif getattr(event, 'button', None) == 1:
            x, y = event.pos
            if "preset_play" in app.ui_elements:
                p = app.ui_elements["preset_play"]
                curr_x = 40 if app.ui_mode == "medium" else p['x_pos']
                hb_w = 15
                if abs(y - p['y_pos']) < 15 and abs(x - curr_x) < hb_w:
                    triggered = True

        if triggered:
            app.preset_play_active = not getattr(app, 'preset_play_active', False)
            if app.preset_play_active:
                app.preset_last_play_time = time.time()
            sync_ui(app)
            return True
        return False

    if not event and update:
        if getattr(app, 'preset_play_active', False):
            current_time = time.time()
            if not hasattr(app, 'preset_last_play_time'):
                app.preset_last_play_time = current_time

            if current_time - app.preset_last_play_time >= 10.0:
                app.preset_last_play_time = current_time
                active_slots = sorted(
                    [str(i) for i in range(1, 10) if hasattr(app, 'presets') and str(i) in app.presets])

                if active_slots:
                    current_slot = getattr(app, 'current_preset_slot', None)
                    next_idx = (active_slots.index(current_slot) + 1) % len(
                        active_slots) if current_slot in active_slots else 0
                    app.current_preset_slot = active_slots[next_idx]
                    settings_manager.toggle_preset(app, active_slots[next_idx])
    return False

def rotate_toggle(app, update=False, event=None):
    if event and _check(app, event, 'R', 'rotate'):
        app.rotate = not getattr(app, 'rotate', False)
        if not app.rotate: app.orbital_root.transform.reset()
        sync_ui(app)
        return True

    if not event:
        if update:
            preset_play_toggle(app, update=True)
            if getattr(app, 'rotate', False):
                app.time += 1.0
                app.orbital_root.transform.reset()
                app.orbital_root.transform.rotate(app.time, (0, 0, 1))
                app.update()

def slice_toggle(app, payloads=None, event=None):
    if event:
        for ax in ['X', 'Y', 'Z']:
            if _check(app, event, ax, f"slice_{ax.lower()}"):
                setattr(app, f"slice_{ax.lower()}", not getattr(app, f"slice_{ax.lower()}"))
                app.refresh_display()
                sync_ui(app)
                return True

        if _check(app, event, 'I', "slice_invert"):
            app.slice_invert = not getattr(app, 'slice_invert', False)
            app.refresh_display()
            sync_ui(app)
            return True
        return False

    if payloads is not None:
        is_inv = getattr(app, 'slice_invert', False)
        any_slice = app.slice_x or app.slice_y or app.slice_z

        filtered = []
        for p in payloads:
            new_p = p.copy()
            pts = new_p["pos"]

            if len(pts) > 0:
                mask = np.ones(len(pts), dtype=bool)

                if app.slice_x: mask &= (pts[:, 0] > 0)
                if app.slice_y: mask &= (pts[:, 1] > 0)
                if app.slice_z: mask &= (pts[:, 2] > 0)

                if is_inv and any_slice:
                    mask = ~mask

                pts = pts[mask]
                if "face_color" in new_p and isinstance(new_p["face_color"], np.ndarray):
                    new_p["face_color"] = new_p["face_color"][mask]

            new_p["pos"] = pts if len(pts) > 0 else np.empty((0, 3))
            filtered.append(new_p)

        vol_mask = None
        if any_slice:
            vol_mask = np.ones((100, 100, 100), dtype=bool)

            if app.slice_x: vol_mask[:50, :, :] = False
            if app.slice_y: vol_mask[:, :50, :] = False
            if app.slice_z: vol_mask[:, :, :50] = False

            if is_inv:
                vol_mask = ~vol_mask

        return filtered, vol_mask

    return None, None

def choose_state_toggle(app, attr=None, delta=0, exact_val=None, event=None):
    if event:
        if getattr(event, 'key', None) and hasattr(event.key, 'name'):
            k = event.key.name

            ku = k.upper()
            if ku == 'TAB':
                app.active_input = ['n', 'l', 'm'][
                    (['n', 'l', 'm'].index(app.active_input) + 1) % 3] if app.active_input in ['n', 'l', 'm'] else 'n'
                app.input_buffer = ""
                sync_ui(app)
                return True
            if app.active_input:
                if k.isdigit() or (k in ['Minus', '-'] and app.active_input == 'm' and not app.input_buffer):
                    app.input_buffer += '-' if k in ['Minus', '-'] else k
                    sync_ui(app)
                    return True
                if k == 'Enter' and app.input_buffer and app.input_buffer != '-':
                    try:
                        choose_state_toggle(app, attr=app.active_input, exact_val=int(app.input_buffer))
                    except ValueError:
                        pass
                    app.active_input, app.input_buffer = None, ""
                    sync_ui(app)
                    return True
                if k == 'Escape':
                    app.active_input, app.input_buffer = None, ""
                    sync_ui(app)
                    return True
                if k == 'Backspace':
                    app.input_buffer = app.input_buffer[:-1]
                    sync_ui(app)
                    return True
            if ku in ['U', 'D']:
                choose_state_toggle(app, attr=app.active_input or 'n', delta=1 if ku == 'U' else -1)
                return True
            if ku == 'B':
                choose_state_toggle(app, attr='basis', delta=1)
                return True
            return False

        if hasattr(event, 'button') and event.button == 1:
            x, y = event.pos
            if app.ui_mode == "hidden" and abs(y - 25) < 15 and 50 <= x <= 180:
                if abs(x - 60) < 15:
                    choose_state_toggle(app, attr='basis', delta=1)
                elif abs(x - 90) < 12:
                    app.active_input, app.input_buffer = 'n', ""
                elif abs(x - 115) < 12:
                    app.active_input, app.input_buffer = 'l', ""
                elif abs(x - 140) < 12:
                    app.active_input, app.input_buffer = 'm', ""
                sync_ui(app)
                return True
            for sid in ["basis", "n", "l", "m"]:
                if abs(y - app.ui_elements.get(f"{sid}_y_pos", -100)) < 15:

                    dx, vx, ux = (50, 130, 210) if app.ui_mode == "full" else (15, 45, 75)
                    r_txt, r_arr = (35, 25) if app.ui_mode == "full" else (14, 14)

                    if abs(x - vx) < r_txt and sid in ["n", "l", "m"]:
                        app.active_input, app.input_buffer = sid, ""
                        sync_ui(app)
                        return True
                    d = -1 if abs(x - dx) < r_arr else (1 if abs(x - ux) < r_arr else 0)
                    if (sid == "l" and app.n == 1) or (sid == "m" and app.l == 0): d = 0
                    if d != 0: choose_state_toggle(app, attr=sid, delta=d)
                    return True
            return False

    if attr == 'basis':
        app.basis = app.basis_modes[(app.basis_modes.index(app.basis) + delta) % len(app.basis_modes)]
    elif attr in ['n', 'l', 'm']:
        if exact_val is not None:
            if attr == 'n':
                app.n = exact_val
            elif attr == 'l':
                app.l = exact_val
            elif attr == 'm':
                app.m = exact_val
        else:
            if attr == 'n':
                app.n = 1 + ((app.n - 1 + delta) % quantum_math.MAX_n)
            elif attr == 'l':
                app.l = (app.l + delta) % app.n
            elif attr == 'm':
                app.m = -app.l + ((app.m + app.l + delta) % (2 * app.l + 1))
        app.n, app.l = max(1, min(app.n, quantum_math.MAX_n)), max(0, min(app.l, app.n - 1))
        app.m = max(-app.l, min(app.m, app.l))
    app.refresh_display()

def randomize_state_toggle(app, event=None):
    if event and _check(app, event, '/', 'random_bg'):
        randomize_state_toggle(app)
        return True
    if not event:
        app.n, app.l, app.m, app.basis = random.choice(
            [(1, 0, 0, 'real'), (2, 0, 0, 'real'), (2, 1, -1, 'real'), (2, 1, 0, 'real'), (2, 1, 1, 'real'),
             (3, 0, 0, 'real'), (3, 1, -1, 'real'),
             (3, 1, 0, 'real'), (3, 1, 1, 'real'), (3, 2, -2, 'real'), (3, 2, -1, 'real'), (3, 2, 0, 'real'),
             (3, 2, 1, 'real'), (3, 2, 2, 'real'),
             (4, 0, 0, 'real'), (4, 1, -1, 'real'), (4, 1, 0, 'real'), (4, 1, 1, 'real'), (4, 2, -2, 'real'),
             (4, 2, -1, 'real'), (4, 2, 0, 'real'),
             (4, 2, 1, 'real'), (4, 2, 2, 'real'), (4, 3, -3, 'real'), (4, 3, -2, 'real'), (4, 3, -1, 'real'),
             (4, 3, 0, 'real'), (4, 3, 1, 'real'),
             (4, 3, 2, 'real'), (4, 3, 3, 'real'), (2, 1, -1, 'comp'), (2, 1, 1, 'comp'), (3, 1, -1, 'comp'),
             (3, 1, 1, 'comp'), (3, 2, -2, 'comp'),
             (3, 2, -1, 'comp'), (3, 2, 1, 'comp'), (3, 2, 2, 'comp'), (4, 1, -1, 'comp'), (4, 1, 1, 'comp'),
             (4, 2, -2, 'comp'), (4, 2, -1, 'comp'),
             (4, 2, 1, 'comp'), (4, 2, 2, 'comp'), (4, 3, -3, 'comp'), (4, 3, -2, 'comp'), (4, 3, -1, 'comp'),
             (4, 3, 1, 'comp'), (4, 3, 2, 'comp'),
             (4, 3, 3, 'comp'), (2, 1, -1, 'imag'), (2, 1, 1, 'imag'), (3, 1, -1, 'imag'), (3, 1, 1, 'imag'),
             (3, 2, -2, 'imag'), (3, 2, -1, 'imag'),
             (3, 2, 1, 'imag'), (3, 2, 2, 'imag'), (4, 1, -1, 'imag'), (4, 1, 1, 'imag'), (4, 2, -2, 'imag'),
             (4, 2, -1, 'imag'), (4, 2, 1, 'imag'),
             (4, 2, 2, 'imag'), (4, 3, -3, 'imag'), (4, 3, -2, 'imag'), (4, 3, -1, 'imag'), (4, 3, 1, 'imag'),
             (4, 3, 2, 'imag'), (4, 3, 3, 'imag')])
        choose_state_toggle(app)

def route_shared_events(app, event):
    toggles = [
        choose_state_toggle, point_cloud_toggle, isosurface_toggle,
        nodes_toggle, axes_toggle, rotate_toggle,
        slice_toggle, randomize_state_toggle, preset_play_toggle]
    return any(t(app, event=event) for t in toggles)

def handle_mouse_press(app, event):
    if route_shared_events(app, event):
        return

    x, y = event.pos
    if abs(y - 25) < 20 and x < 40 and event.button == 1:
        app.ui_mode = ["full", "medium", "hidden"][(["full", "medium", "hidden"].index(app.ui_mode) + 1) % 3]
        update_layout_mode(app)
        return

    if event.button == 1 and abs(y - 25) < 15:
        if app.ui_mode == "full" and abs(x - 260) < 30:
            aesthetics.open_help_menu(app)
            return
        if app.ui_mode == "medium" and abs(x - 65) < 15:
            aesthetics.open_help_menu(app)
            return

    for i in range(1, 10):
        if f"preset_{i}" in app.ui_elements:
            p = app.ui_elements[f"preset_{i}"]

            curr_x = 10 + ((i - 1) % 3) * 30 if app.ui_mode == "medium" else p['x_pos']
            hb_w = 15 if app.ui_mode == "medium" else 35

            if abs(y - p['y_pos']) < 15 and abs(x - curr_x) < hb_w:
                if event.button == 2:
                    settings_manager.delete_preset(app, str(i))
                else:
                    settings_manager.toggle_preset(app, str(i))
                    app.current_preset_slot = str(i)
                return

    if app.ui_mode == "medium" and event.button == 1:
        med_y = app.ui_elements.get("color_btn_y", 0)
        if abs(y - med_y) < 20:
            if abs(x - 20) < 15:
                aesthetics.open_color_menu(app)
                return
            if abs(x - 60) < 15:
                aesthetics.open_background_menu(app)
                return

    if app.ui_mode == "full" and event.button == 1:
        if abs(y - app.ui_elements.get("color_btn_y", 0)) < 20 and abs(x - 50) < 40:
            aesthetics.open_color_menu(app)
            return
        if abs(y - app.ui_elements.get("bg_btn_y", 0)) < 20 and abs(x - 200) < 70:
            aesthetics.open_background_menu(app)
            return

    if x > (320 if app.ui_mode == "full" else 90): app.active_input, app.input_buffer = None, ""
    sync_ui(app)

def handle_key_press(app, event):
    if route_shared_events(app, event):
        return

    if not hasattr(event.key, 'name'):
        return
    k = event.key.name

    if k in '123456789':
        if len(event.modifiers) > 0 and any(m.name == 'Control' for m in event.modifiers):
            settings_manager.delete_preset(app, k)
        else:
            settings_manager.toggle_preset(app, k)
            app.current_preset_slot = k
        return

    if k == 'H':
        import aesthetics
        aesthetics.open_help_menu(app)
        return

    if k == 'C':
        import aesthetics
        aesthetics.open_color_menu(app)
        return

    if k == 'E':
        import aesthetics
        aesthetics.open_background_menu(app)
        return

    elif k.upper() == 'M':
        app.ui_mode = ["full", "medium", "hidden"][(["full", "medium", "hidden"].index(app.ui_mode) + 1) % 3]
        update_layout_mode(app)

    if k == 'Escape' and hasattr(event, 'handled'): event.handled = True
