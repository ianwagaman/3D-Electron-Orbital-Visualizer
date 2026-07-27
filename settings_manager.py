import json
import os


def get_settings_path():
    """
    Locates the standard AppData directory, creates a folder for the app,
    and returns the absolute path for settings.json.
    """
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    app_dir = os.path.join(appdata, "OrbitalViewer")
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "settings.json")


def save_settings(app):
    try:
        # Safely extract background index if manager exists
        bg_idx = 0
        if hasattr(app, 'bg_manager'):
            bg_idx = getattr(app.bg_manager, 'bg_index', 0)

        data = {
            "presets": getattr(app, 'presets', {}),
            "colors": getattr(app, 'custom_colors', {}),
            "bg_index": bg_idx,
            "toggles": {
                "show_points": getattr(app, 'show_points', True),
                "show_surfaces": getattr(app, 'show_surfaces', True),
                "show_nodes": getattr(app, 'show_nodes', False),
                "show_axes": getattr(app, 'show_axes', False),
                "slice_x": getattr(app, 'slice_x', False),
                "slice_y": getattr(app, 'slice_y', False),
                "slice_z": getattr(app, 'slice_z', False),
                "slice_invert": getattr(app, 'slice_invert', False)},
            "current_state": {
                "n": getattr(app, 'n', 1),
                "l": getattr(app, 'l', 0),
                "m": getattr(app, 'm', 0),
                "basis": getattr(app, 'basis', 'real'),
                "ui_mode": getattr(app, 'ui_mode', 'full')}}

        settings_path = get_settings_path()
        with open(settings_path, 'w') as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        # If run without --noconsole, this will print why it failed instead of crashing silently
        print(f"Failed to save settings: {e}")


def load_settings(app):
    settings_path = get_settings_path()

    if not os.path.exists(settings_path):
        app.presets = {}
        app.custom_colors = {}
        return

    try:
        with open(settings_path, 'r') as f:
            data = json.load(f)

        app.presets = data.get("presets", {})
        app.custom_colors = data.get("colors", {})

        toggles = data.get("toggles", {})
        app.show_points = toggles.get("show_points", True)
        app.show_surfaces = toggles.get("show_surfaces", True)
        app.show_nodes = toggles.get("show_nodes", False)
        app.show_axes = toggles.get("show_axes", False)
        app.slice_x = toggles.get("slice_x", False)
        app.slice_y = toggles.get("slice_y", False)
        app.slice_z = toggles.get("slice_z", False)
        app.slice_invert = toggles.get("slice_invert", False)

        state = data.get("current_state", {})
        if state:
            app.n = state.get("n", 1)
            app.l = state.get("l", 0)
            app.m = state.get("m", 0)
            app.basis = state.get("basis", 'real')

        app.rotate = False

        import ui_logic
        ui_logic.update_layout_mode(app)

        if hasattr(app, 'bg_manager'):
            bg_index = data.get("bg_index", 0)
            app.bg_manager.set_background(bg_index)

            init_bg = app.custom_colors.get("scene_bg", "#000000")
            if hasattr(app, 'bg_view'):
                app.bg_view.bgcolor = init_bg
            else:
                app.bgcolor = init_bg
    except Exception as e:
        print(f"Failed to load settings: {e}")


def toggle_preset(app, slot):
    slot = str(slot)
    if slot in app.presets:
        state = app.presets[slot]
        app.n, app.l, app.m, app.basis = state['n'], state['l'], state['m'], state['basis']
    else:
        app.presets[slot] = {"n": app.n, "l": app.l, "m": app.m, "basis": app.basis}
        save_settings(app)

    app.refresh_display()
    import ui_logic
    ui_logic.sync_ui(app)


def delete_preset(app, slot):
    slot = str(slot)
    if slot in app.presets:
        del app.presets[slot]
        save_settings(app)
        import ui_logic
        ui_logic.sync_ui(app)