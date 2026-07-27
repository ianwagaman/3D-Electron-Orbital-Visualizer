from vispy import scene, app as vispy_app
from vispy.scene import cameras
import numpy as np
import os
import sys
import ui_logic, settings_manager, aesthetics
import orbitals

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class OrbitalApp(scene.SceneCanvas):
    def __init__(self):
        super().__init__(keys=None, config={'depth_size': 24})

        self.unfreeze()

        self.custom_colors = {}
        self.presets = {}

        # State Variables
        self.n, self.l, self.m = 1, 0, 0
        self.last_n = None  # Added for zoom fix
        self.basis = "real"
        self.active_input = None
        self.input_buffer = ""
        self.show_points = True
        self.show_surfaces = True
        self.show_nodes = False
        self.show_axes = False
        self.rotate = False
        self.basis_modes = ["real", "imag", "comp"]
        self.slice_x = self.slice_y = self.slice_z = False
        self.slice_invert = False
        self.time = 0.0
        self.pos_meshes = []
        self.neg_meshes = []
        self.node_visuals = []

        self.ui_mode = "full"
        self.auto_resize = True

        # Initialize bg_view BEFORE the main view so it renders underneath
        self.bg_view = self.central_widget.add_view()
        self.bg_view.interactive = False  # Ignore mouse events
        self.bg_view.camera = 'panzoom'

        self.view = self.central_widget.add_view()
        self.view.camera = cameras.ArcballCamera(distance=22)

        self.bg_manager = aesthetics.BackgroundMenu(self)
        self.bg_manager.initialize_background()

        self.orbital_root = scene.Node(parent=self.view.scene)
        self.orbital_root.transform = scene.transforms.MatrixTransform()
        self.ui_container = scene.Node(parent=self.scene)

        self.raw_pts_payloads = [{"pos": np.empty((0, 3))}, {"pos": np.empty((0, 3))}]
        self.scatter_pos = scene.visuals.Markers(parent=self.orbital_root)
        self.scatter_neg = scene.visuals.Markers(parent=self.orbital_root)

        self.axes_visual = scene.visuals.XYZAxis(parent=self.view.scene)
        self.axes_visual.visible = False

        # UI Setup
        self.ui_elements = {}
        ui_logic.setup_ui(self)

        settings_manager.load_settings(self)
        ui_logic.sync_ui(self)

        self.timer = vispy_app.Timer('auto', connect=self.on_timer, start=True)
        self._color_menu = None
        self._bg_menu = None

        # Bind events directly to ui_logic, eliminating wrapper functions
        self.events.mouse_press.connect(lambda e: ui_logic.handle_mouse_press(self, e))
        self.events.key_press.connect(lambda e: ui_logic.handle_key_press(self, e))

        self.freeze()

    def on_timer(self, event):
        ui_logic.rotate_toggle(self, update=True)

    def _hex_to_rgba(self, hex_str, alpha=0.5):
        h = hex_str.lstrip('#')
        if len(h) != 6: return (1.0, 1.0, 1.0, alpha)
        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) + (alpha,)

    def refresh_display(self):
        zoom_mapping = {1: 22, 2: 36, 3: 56, 4: 80}
        target_distance = zoom_mapping.get(self.n, 18)

        # Only autoscale if the n value has changed
        if getattr(self, 'last_n', None) != self.n:
            if hasattr(self, 'view') and self.view.camera:
                self.view.camera.distance = target_distance

            if hasattr(self, 'bg_view') and hasattr(self.bg_view.camera, 'distance'):
                self.bg_view.camera.distance = target_distance

            self.last_n = self.n

        for mesh in self.pos_meshes: mesh.parent = None
        for mesh in self.neg_meshes: mesh.parent = None
        for nv in self.node_visuals: nv.parent = None
        self.pos_meshes.clear()
        self.neg_meshes.clear()
        self.node_visuals.clear()

        pos_pts_rgba = self._hex_to_rgba(self.custom_colors.get('pos_pts', '#ff0000'), alpha=0.7)
        neg_pts_rgba = self._hex_to_rgba(self.custom_colors.get('neg_pts', '#0000ff'), alpha=0.7)
        pos_surf_rgba = self._hex_to_rgba(self.custom_colors.get('pos_surf', '#ff0000'), alpha=0.3)
        neg_surf_rgba = self._hex_to_rgba(self.custom_colors.get('neg_surf', '#0000ff'), alpha=0.3)
        node_rgba = self._hex_to_rgba(self.custom_colors.get('nodes', '#ffff00'), alpha=0.2)

        orbitals.nodes(self.n, self.l, self.m, self.basis, self.orbital_root, self.node_visuals, node_rgba)

        self.raw_pts_payloads = orbitals.point_cloud(self.n, self.l, self.m, self.basis, pos_pts_rgba, neg_pts_rgba)
        filtered, mask = ui_logic.slice_toggle(self, self.raw_pts_payloads)
        self.scatter_pos.set_data(**filtered[0])
        self.scatter_neg.set_data(**filtered[1])

        # Unpack the two separated lists returned by your updated isosurfaces function
        pos_surfaces, neg_surfaces = orbitals.isosurfaces(
            self.n, self.l, self.m, self.basis, pos_surf_rgba, neg_surf_rgba, mask=mask
        )

        # Iterate and assign the positive meshes directly (tuples were stripped out in orbitals.py)
        for visual in pos_surfaces:
            visual.parent = self.orbital_root
            self.pos_meshes.append(visual)

        # Iterate and assign the negative meshes directly
        for visual in neg_surfaces:
            visual.parent = self.orbital_root
            self.neg_meshes.append(visual)

        ui_logic.point_cloud_toggle(self)
        ui_logic.isosurface_toggle(self)
        ui_logic.nodes_toggle(self)
        ui_logic.axes_toggle(self)
        ui_logic.sync_ui(self)

        self._apply_render_states()

    def on_resize(self, event):
        if event.size[0] < 10 or event.size[1] < 10:
            return

        super().on_resize(event)
        ui_logic.update_layout_mode(self)
        self.update()

    def _apply_render_states(self):
        for child in self.scene.children:
            if hasattr(child, 'set_gl_state'):
                child.set_gl_state(depth_test=False)

        if hasattr(self, 'axes_visual'):
            self.axes_visual.set_gl_state(depth_test=False)
        if hasattr(self, 'axis_labels'):
            for lbl in self.axis_labels.values():
                lbl.set_gl_state(depth_test=False)

        if hasattr(self, 'scatter_pos'):
            self.scatter_pos.set_gl_state(depth_test=True, depth_mask=False)
        if hasattr(self, 'scatter_neg'):
            self.scatter_neg.set_gl_state(depth_test=True, depth_mask=False)

        for mesh in self.pos_meshes:
            mesh.set_gl_state('translucent', depth_test=True, depth_mask=True, cull_face=False)
        for mesh in self.neg_meshes:
            mesh.set_gl_state('translucent', depth_test=True, depth_mask=True, cull_face=False)

        for node in self.node_visuals:
            node.set_gl_state('translucent', depth_test=True, depth_mask=False, cull_face=False)
