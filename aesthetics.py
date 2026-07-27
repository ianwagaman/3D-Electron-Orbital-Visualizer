from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QColorDialog, QTabWidget, QWidget, \
    QTextEdit
from PyQt6.QtGui import QColor
from vispy import scene
import numpy as np
import settings_manager


class ColorMenu(QDialog):
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app = app_instance
        self.setWindowTitle("Color Menu")
        self.setMinimumWidth(250)
        self.layout = QVBoxLayout(self)

        self.options = [
            ("Positive Points", "pos_pts", "#ff0000"),
            ("Negative Points", "neg_pts", "#0000ff"),
            ("Positive Surface", "pos_surf", "#ff0000"),
            ("Negative Surface", "neg_surf", "#0000ff"),
            ("Nodal Boundary", "nodes", "#ffff00")
        ]

        self.color_widgets = []

        for label_text, key, default_hex in self.options:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            row.addWidget(lbl)

            btn = QPushButton()
            btn.setFixedSize(24, 24)
            initial_color = self.app.custom_colors.get(key, default_hex)
            btn.setStyleSheet(f"background-color: {initial_color}; border: 1px solid #777;")
            btn.clicked.connect(lambda checked, k=key, b=btn: self.pick_color(k, b))

            row.addWidget(btn)
            self.layout.addLayout(row)
            self.color_widgets.append((key, lbl, btn, default_hex))

        self.update_ui_visibility()

    def update_ui_visibility(self):
        for key, lbl, btn, default_hex in self.color_widgets:
            lbl.setStyleSheet("")
            btn.setEnabled(True)
            btn.setText("")
            color = self.app.custom_colors.get(key, default_hex)
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid #777;")

    def pick_color(self, key, btn):
        current_hex = self.app.custom_colors.get(key, "#ffffff")
        dialog = QColorDialog(QColor(current_hex), self)
        dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog)
        dialog.currentColorChanged.connect(lambda color: self.live_update(key, color, btn))

        if dialog.exec():
            self.app.custom_colors[key] = dialog.selectedColor().name()
            import settings_manager
            settings_manager.save_settings(self.app)
            self.update_ui_visibility()
        else:
            self.live_update(key, QColor(current_hex), btn)

    def live_update(self, key, qcolor, btn):
        hex_color = qcolor.name()
        btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #777;")
        self.app.custom_colors[key] = hex_color
        self.app.refresh_display()

def open_color_menu(app):
    if getattr(app, '_color_menu', None) is None:
        app._color_menu = ColorMenu(app, parent=app.native)
    else:
        app._color_menu.update_ui_visibility()

    if not app._color_menu.isVisible():
        app._color_menu.show()
    else:
        app._color_menu.raise_()
        app._color_menu.activateWindow()


class BackgroundMenu(QDialog):
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app = app_instance
        self.setWindowTitle("Environment Menu")
        self.setMinimumWidth(250)
        self.layout = QVBoxLayout(self)

        self.bg_index = 0
        self.grid_visual = None
        self.current_x_offset = 0

        self.bg_generators = [
            self.create_off,
            self.create_simple_floor,
            self.create_gap_grid,
            self.create_room_grid,
            self.create_box_tunnel
        ]

        # Scene Background Color Picker
        scene_bg_row = QHBoxLayout()
        scene_bg_row.addWidget(QLabel("Background Color"))
        self.scene_bg_btn = QPushButton()
        self.scene_bg_btn.setFixedSize(24, 24)
        current_scene_bg = self.app.custom_colors.get("scene_bg", "#000000")
        self.scene_bg_btn.setStyleSheet(f"background-color: {current_scene_bg}; border: 1px solid #777;")
        self.scene_bg_btn.clicked.connect(self.pick_scene_color)
        scene_bg_row.addWidget(self.scene_bg_btn)
        self.layout.addLayout(scene_bg_row)

        # Grid Color Picker
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Grid Color"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(24, 24)
        current_color = self.app.custom_colors.get("bg_grid", "#00ffff")
        self.color_btn.setStyleSheet(f"background-color: {current_color}; border: 1px solid #777;")
        self.color_btn.clicked.connect(self.pick_color)
        color_row.addWidget(self.color_btn)
        self.layout.addLayout(color_row)

        self.buttons = ["Off", "Floor Grid", "Split Double Grid", "Double Grid", "Box Grid"]
        for i, name in enumerate(self.buttons):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, idx=i: self.set_background(idx))
            self.layout.addWidget(btn)

        self.app.events.resize.connect(self.refresh_grid)

    def pick_scene_color(self):
        current_hex = self.app.custom_colors.get("scene_bg", "#000000")
        dialog = QColorDialog(QColor(current_hex), self)
        dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog)
        dialog.currentColorChanged.connect(self.live_update_scene_color)

        if dialog.exec():
            self.app.custom_colors["scene_bg"] = dialog.selectedColor().name()
            settings_manager.save_settings(self.app)
        else:
            self.live_update_scene_color(QColor(current_hex))

    def live_update_scene_color(self, qcolor):
        new_color = qcolor.name()
        self.scene_bg_btn.setStyleSheet(f"background-color: {new_color}; border: 1px solid #777;")
        self.app.custom_colors["scene_bg"] = new_color

        # Color the specific view instead of the global canvas
        if hasattr(self.app, 'bg_view'):
            self.app.bg_view.bgcolor = new_color
        else:
            self.app.bgcolor = new_color
        self.app.update()

    def pick_color(self):
        current_hex = self.app.custom_colors.get("bg_grid", "#00ffff")
        dialog = QColorDialog(QColor(current_hex), self)
        dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog)
        dialog.currentColorChanged.connect(self.live_update_grid_color)

        if dialog.exec():
            self.app.custom_colors["bg_grid"] = dialog.selectedColor().name()
            settings_manager.save_settings(self.app)
        else:
            self.live_update_grid_color(QColor(current_hex))

    def live_update_grid_color(self, qcolor):
        new_color = qcolor.name()
        self.color_btn.setStyleSheet(f"background-color: {new_color}; border: 1px solid #777;")
        self.app.custom_colors["bg_grid"] = new_color

        if self.grid_visual:
            c = self.hex_to_rgba(new_color, 0.5)
            self.grid_visual.set_data(color=c)
        self.app.update()

    def initialize_background(self):
        init_bg = self.app.custom_colors.get("scene_bg", "#000000")
        if hasattr(self.app, 'bg_view'):
            self.app.bg_view.bgcolor = init_bg
        else:
            self.app.bgcolor = init_bg
        self.set_background(0)

    def set_background(self, index):
        self.bg_index = index

        if index == 0:
            if self.grid_visual:
                self.grid_visual.visible = False
            self.app.update()
            return

        if not self.grid_visual:
            c = self.hex_to_rgba(self.app.custom_colors.get("bg_grid", "#00ffff"), 0.5)
            # Parent the lines to the new view
            parent_node = self.app.bg_view.scene if hasattr(self.app, 'bg_view') else self.app.scene
            self.grid_visual = scene.visuals.Line(color=c, connect='segments', parent=parent_node)
            self.grid_visual.set_gl_state(depth_test=False)
            self.grid_visual.order = -100

        self.grid_visual.visible = True
        self.refresh_grid()

    def _clip_lines(self, lines, x, y, w, h):
        """ Cohen-Sutherland line clipping algorithm to ensure lines never draw under the UI."""
        clipped = []
        xmin, ymin, xmax, ymax = x, y, x + w, y + h
        INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

        def compute_outcode(px, py):
            code = INSIDE
            if px < xmin:
                code |= LEFT
            elif px > xmax:
                code |= RIGHT
            if py < ymin:
                code |= BOTTOM
            elif py > ymax:
                code |= TOP
            return code

        for line in lines:
            x0, y0 = line[0]
            x1, y1 = line[1]
            outcode0 = compute_outcode(x0, y0)
            outcode1 = compute_outcode(x1, y1)
            accept = False

            while True:
                if not (outcode0 | outcode1):
                    accept = True
                    break
                elif outcode0 & outcode1:
                    break
                else:
                    cx, cy = 0.0, 0.0
                    outcode_out = outcode1 if outcode1 > outcode0 else outcode0
                    dx = x1 - x0
                    dy = y1 - y0

                    if outcode_out & TOP:
                        cx = x0 + dx * (ymax - y0) / dy if dy != 0 else x0
                        cy = ymax
                    elif outcode_out & BOTTOM:
                        cx = x0 + dx * (ymin - y0) / dy if dy != 0 else x0
                        cy = ymin
                    elif outcode_out & RIGHT:
                        cy = y0 + dy * (xmax - x0) / dx if dx != 0 else y0
                        cx = xmax
                    elif outcode_out & LEFT:
                        cy = y0 + dy * (xmin - x0) / dx if dx != 0 else y0
                        cx = xmin

                    if outcode_out == outcode0:
                        x0, y0 = cx, cy
                        outcode0 = compute_outcode(x0, y0)
                    else:
                        x1, y1 = cx, cy
                        outcode1 = compute_outcode(x1, y1)

            if accept:
                clipped.append([[x0, y0], [x1, y1]])

        return clipped

    def refresh_grid(self, event=None, t_width=None, w=None, h=None):
        if self.bg_index == 0 or not self.grid_visual:
            return

        canvas_w, canvas_h = self.app.size

        if t_width is not None:
            self.current_x_offset = t_width
        elif hasattr(self.app, 'ui_width'):
            self.current_x_offset = self.app.ui_width

        draw_w = max(1, canvas_w - self.current_x_offset)
        draw_h = max(1, canvas_h)

        if hasattr(self.app, 'bg_view'):
            # Match standard pixel coordinate system (y inverted so 0 is top)
            self.app.bg_view.camera.set_range(x=(0, draw_w), y=(draw_h, 0), margin=0)

            # Generate starting from 0; bg_view is inherently shifted over the UI offset
            lines = self.bg_generators[self.bg_index](0, 0, draw_w, draw_h)
            clipped_lines = lines  # Native view bounds handle clipping implicitly
        else:
            lines = self.bg_generators[self.bg_index](self.current_x_offset, 0, draw_w, draw_h)
            clipped_lines = self._clip_lines(lines, self.current_x_offset, 0, draw_w, draw_h)

        if not clipped_lines:
            self.grid_visual.set_data(pos=np.empty((0, 2), dtype=np.float32))
        else:
            data = np.array(clipped_lines, dtype=np.float32).reshape(-1, 2)
            self.grid_visual.set_data(pos=data)

        self.app.update()

    def hex_to_rgba(self, hex_color, alpha=0.5):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        return (r * alpha, g * alpha, b * alpha, 1.0)

    def _build_plane(self, x, y, w, h, divisions, direction=1, gap_px=0):
        lines = []
        center_x = x + (w / 2.0)
        center_y = y + (h / 2.0)

        horizon_y = center_y + (gap_px * direction)
        edge_y = y + h if direction == 1 else y

        far_width = w * 0.5
        near_width = w * 1.5

        for i in range(divisions + 1):
            t = i / divisions
            xf = center_x - far_width + (2 * far_width) * t
            xn = center_x - near_width + (2 * near_width) * t
            lines.append([[xf, horizon_y], [xn, edge_y]])

        num_h = 35
        z_steps = np.linspace(0, 1, num_h) ** 2.0
        for z in z_steps:
            y_pos = horizon_y + z * (edge_y - horizon_y)
            current_half_width = far_width + z * (near_width - far_width)
            lines.append([[center_x - current_half_width, y_pos], [center_x + current_half_width, y_pos]])

        return lines

    def create_off(self, x, y, w, h):
        return []

    def create_simple_floor(self, x, y, w, h):
        return self._build_plane(x, y, w, h, 40, direction=1, gap_px=0)

    def create_gap_grid(self, x, y, w, h):
        lines = self._build_plane(x, y, w, h, 40, direction=1, gap_px=80)
        lines += self._build_plane(x, y, w, h, 40, direction=-1, gap_px=80)
        return lines

    def create_room_grid(self, x, y, w, h):
        lines = self._build_plane(x, y, w, h, 40, direction=1, gap_px=0)
        lines += self._build_plane(x, y, w, h, 40, direction=-1, gap_px=0)
        return lines

    def create_box_tunnel(self, x, y, w, h):
        lines = []
        center_x = x + (w / 2.0)
        center_y = y + (h / 2.0)

        near_width = w * 1.5
        near_height = h * 1.5

        # Corner diagonals
        corners = [
            (center_x - near_width, center_y - near_height),
            (center_x + near_width, center_y - near_height),
            (center_x + near_width, center_y + near_height),
            (center_x - near_width, center_y + near_height)
        ]
        for cx, cy in corners:
            lines.append([[cx, cy], [center_x, center_y]])

        # Radial spokes for grid perspective
        num_spokes = 8
        for t in np.linspace(-1, 1, num_spokes + 2)[1:-1]:
            # Top and Bottom
            lines.append([[center_x + t * near_width, center_y - near_height], [center_x, center_y]])
            lines.append([[center_x + t * near_width, center_y + near_height], [center_x, center_y]])
            # Left and Right
            lines.append([[center_x - near_width, center_y + t * near_height], [center_x, center_y]])
            lines.append([[center_x + near_width, center_y + t * near_height], [center_x, center_y]])

        # Concentric shrinking rectangles
        num_rects = 35
        z_steps = np.linspace(0, 1, num_rects) ** 2.0
        for z in z_steps:
            if z == 0: continue
            cw = z * near_width
            ch = z * near_height
            lines.append([[center_x - cw, center_y - ch], [center_x + cw, center_y - ch]])
            lines.append([[center_x - cw, center_y + ch], [center_x + cw, center_y + ch]])
            lines.append([[center_x - cw, center_y - ch], [center_x - cw, center_y + ch]])
            lines.append([[center_x + cw, center_y - ch], [center_x + cw, center_y + ch]])

        return lines

def open_background_menu(app):
    current_color = app.custom_colors.get("bg_grid", "#00ffff")
    app.bg_manager.color_btn.setStyleSheet(f"background-color: {current_color}; border: 1px solid #777;")

    current_scene = app.custom_colors.get("scene_bg", "#000000")
    app.bg_manager.scene_bg_btn.setStyleSheet(f"background-color: {current_scene}; border: 1px solid #777;")

    if not app.bg_manager.isVisible():
        app.bg_manager.show()
    else:
        app.bg_manager.raise_()
        app.bg_manager.activateWindow()


class HelpMenu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Information & Guide")
        self.resize(500, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: #cccccc;")

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        help_content = {
            "The Controls": "For the 3D electron orbital displayed, you can scroll to zoom, and drag to rotate.<br><br>"
                            "<u>User Interface:</u><br> "
                            "<b>• =:</b> Changes the UI mode.<br> "
                            "<b>• Help:</b> Opens a window with information about this program. (How did you get here if I didn't tell you what clicking that button did?)<br> "
                            "<b>• Point Cloud:</b> Toggles the point cloud.<br> "
                            "<b>• Orbital Isosurface:</b> Toggles the orbital isosurfaces.<br> "
                            "<b>• Nodal Boundary:</b> Toggles the nodes.<br> "
                            "<b>• Coordinate Axes:</b> Toggles the X, Y, and Z axes.<br> "
                            "<b>• Rotate:</b> Rotates the orbital around the Z-axis.<br> "
                            "<b>• Slice X-Axis:</b> Removes half of the orbital along the X-axis.<br>"
                            "<b>• Slice Y-Axis:</b> Removes half of the orbital along the Y-axis.<br> "
                            "<b>• Slice Z-Axis:</b> You get exactly <b>0</b> guesses what this button does.<br> "
                            "<b>• Randomize:</b> Displays a random state.<br>"
                            "<b>• <B>, <n>, <l>, <m>:</b> Clicking the arrows changes the basis or increments the value.<br>"
                            "<b>• n, l, m :</b> Clicking the letters allows you to input the specific quantum numbers. Only acceptable combinations will work, and you should input numbers from top to bottom (first n, then l, lastly m).<br>"
                            "<b>• Left Click on #B|nlm> Presets:</b> Sets a new preset or goes to a saved preset.<br>"
                            "<b>• Right Click on #B|nlm> Presets:</b> Resets a preset.<br>"
                            "<b>• >: Cycles through all presets, switching every 10 seconds.<br>"
                            "<b>• Colors:</b> Opens a menu that lets you choose the colors of the points, the surfaces, and the nodes.<br> "
                            "<b>• Environment:</b> Opens a menu that lets you set an environment and change its color.<br><br>"
                            "<u>Keyboard Shortcuts:</u><br>"
                            "<b>• P:</b> Toggles the point cloud.<br>"
                            "<b>• S:</b> Toggles the isosurfaces.<br>"
                            "<b>• N:</b> Toggles the nodes.<br>"
                            "<b>• A:</b> Toggles the X, Y, and Z axes.<br>"
                            "<b>• X/Y/Z:</b> Toggles planar slices.<br>"
                            "<b>• M:</b> Changes the UI mode.<br>"
                            "<b>• R:</b> Toggles rotation.<br>"
                            "<b>• /:</b> Displays a random state. (I used this for random because '?' is on the same key.)<br>"
                            "<b>• B:</b> Changes the basis.<br>"
                            "<b>• C:</b> Opens the Color menu.<br>"
                            "<b>• E:</b> Opens the Environment menu.<br>"
                            "<b>• I:</b> Invert the currently applied slices (1/4 <-> 3/4 or 1/8 <-> 7/8).<br>"
                            "<b>• H:</b> Opens the Help menu.<br>"
                            "<b>• TAB:</b> Cycles active input between n, l, and m. You can then use numbers or U / D.<br>"
                            "<b>• U / D:</b> Increases or decreases the currently active quantum number.<br>"
                            "<b>• 1-4:</b> Inputs a number <u>after clicking or using TAB to get to a quantum number (n, l, m)</u>. Maxes out at n = 4. (n > l &ge; |m|)<br>"
                            "<b>• - [minus]:</b> Makes m values negative.<br>"
                            "<b>• 1-9:</b> Sets a new preset or goes to a saved preset.<br>"
                            "<b>• Ctrl + 1-9:</b> Removes a saved preset.<br>"
                            "<b>• Enter:</b> Confirms the current input value to change the state.<br>"
                            "<b>• Escape:</b> Cancels any changes to the quantum numbers.<br>"
                            "<b>• Backspace:</b> Removes the an input character.<br>"
                            "<b>• Spacebar:</b> Cycles through all presets, switching every 10 seconds.",

            "The Basics": "This program displays electron orbitals. Adjust the quantum numbers (n, l, m) to explore different states. Change the basis "
                          "from 'Real' to 'Imaginary' to 'Complex' to view the different components from the factor e<sup>im&phi;</sup> = cos(m&phi;) + i*sin(m&phi;). "
                          "In the real basis, the imaginary sine portion is removed, while in the imaginary basis, the real cosine portion is removed. Note that "
                          "if m=0, the imaginary contribution is zero, resulting in an empty screen as a reminder of the math (i*sin(0*&phi;) = 0). The complex "
                          "basis combines both of those components, except for when m=0, which will just show you the real component. I recommend using the phase"
                          "coloring for the complex basis and turning on rotation because this shows how the wavefunction's phase evolves over time, which controls "
                          "an atom’s bonding behaviour. I have implemented two ways to visualize the orbitals. The isosurfaces are like borders around high probability "
                          "regions, while the point clouds are just random assortments of points that an electron might be at. The isosurfaces should extend "
                          "infinitely, but I just picked a low probability value and set it to 0, so that you see shapes rather than just a glowing expanse with no "
                          "detail. These electron orbitals are probabilistic structures. The point cloud is similar to looking at a map without drawn borders. "
                          "Separate regions are understood to exist, even without an explicit boundary. A single orbital can only hold up to two electrons, as "
                          "long as they have different spin values. There are also two distinct color modes available. The 'Signed' mode visualizes the positive "
                          "and negative regions of the wavefunction. To be clear, these signs refer to math, not electric charge. The 'Phase' mode is particularly "
                          "useful with the rotation feature for complex orbitals, where the phase is always moving. The phase controls where atoms can bond at any given "
                          "moment, with some regions being open to bonding, and some completely rejecting bonds. You will also find nodes, which are the 'no-go' zones "
                          "where the probability drops to 0, and coordinate axes to help you orient yourself in 3D space. Slicing the X, Y, and Z axes lets you see the "
                          "interior layers of the higher level orbitals better. You can save nine different configurations with the numbered buttons to bring you "
                          "directly to them, and the play button will cycle through your saved orbitals like a slideshow. The 'Randomize' button is just a fun way "
                          "to encounter the variety of orbitals here. Finally, you can change the colors and backgrounds too. Combine those aesthetic options with your "
                          "presets, the rotation toggle, and the minimized UI to get a screensaver/wallpaper mode. Have fun!",

            "More Detail": "Every energy level (n value) above the ground state (n=1) has multiple overlapping orbitals that combine to make a 'shell'. Every orbital "
                           "only holds 2 electrons. A spin up electron, and a spin down electron because the Pauli Exclusion Principle does not allow for electrons to "
                           "inhabit the same location unless they are unique. In quantum mechanics, this 'spin' has nothing to do with spinning in the way you are "
                           "thinking about. It is a poorly named intrinsic property of an electron, kind of like how you have a hair color, eye color, blood type, and "
                           "so on. I will not elaborate further on 'spin' because I am trying to keep things simple. Anyways, while almost every orbital isosurface "
                           "has at least two regions, that has no bearing on the number of electrons it holds. If that was the case, then the 1s orbital would only hold "
                           "one electron, but this is not true.<br><br>"

                           "Moving on, electrons are not in a specific location. Orbitals are probability maps, not tangible boundaries that contain electrons, and "
                           "not a smattering of particles either. All the representations can be useful, whether you change the basis, or look at the isosurfaces "
                           "vs the point clouds, but they also can mislead you if you take them too literally. Isosurfaces are like boundaries for where the electron "
                           "could be around an atom. Also, let’s quickly define 'isosurfaces'. These are just smooth surfaces with the same (iso) probability value "
                           "on the surface. Within the isosurfaces are higher probabilities, and outside of them are lower probabilities. Every point in a cloud is a "
                           "possible electron with a probability of being in that spot. It is not at any of those spots. It is not rapidly teleporting between them. "
                           "It is a wave until it needs to be a particle. When it comes to nodes, an electron can NEVER be there because the probability value "
                           "associated with that location is always zero. Also, I didn't draw a node around the orbitals because they actually go on forever, and "
                           "the probability decreases asymptotically towards 0. They end because I just set anything lower than a specific probability value to 0. "
                           "If I didn't do this, the screen would just show a glowing expanse that goes on forever.<br><br>"

                           "Electrons are in probability space. Maybe here, maybe there, maybe here again. For lone atoms, the complex orbital is the most realistic "
                           "option. Electrons are in superposition within real or imaginary orbitals, but the real and imaginary orbitals within a shell are in "
                           "superposition to make the complex orbitals. You can have an equivalent viewpoint that the complex orbitals are in a superposition that "
                           "can lead to the real and imaginary orbitals, but that is more important for bonding in chemistry. Don’t worry, you’ll learn what I mean "
                           "when you see the math one day and still be confused! We are working with lone atoms here, so let’s stick with the first version of this "
                           "story. You can add up the real and imaginary 2px, 2py and 2pz orbitals to get the complex 2p orbital (and there are 2 versions depending "
                           "on if you use m=1 or m=-1). Viewing the components separately is like taking something apart to see how it works. For example, all the "
                           "pieces of a watch are nothing like a watch on their own, but seeing a working watch doesn’t tell you much about the individual pieces either. "
                           "While I use the mathematical definition of 'real', I’m using the physics definitions of &theta; and &phi; for spherical coordinates and "
                           "spherical harmonics. Other sources will call anything a ‘real’ orbital as long as it is not complex, and I can see where they are going, "
                           "but I’d rather just label the equations based on the common math definitions. If you change the basis from 'Real' to 'Imaginary', then you "
                           "will actually see an orthogonal (it's like 'perpendicular', but also like 'unique', and has an abyss of other mathematical context, too) "
                           "state. To make this basis stuff clear, the orbital equations incorporate Euler's formula as shown: e<sup>im&phi;</sup> = cos(m&phi;) + i*sin(m&phi;), "
                           "leading to their complex nature. This means that when m=0, there is no imaginary contribution, leading to a blank screen when focused on "
                           "the imaginary basis. And when focused on the complex basis, this means that you will just see a real orbital. Also, the complex orbitals "
                           "have a rainbow color scheme to try to help you understand the phase of the orbital. When you activate the rotation feature for a complex "
                           "orbital, the shape is constant in space, but the colors within it are changing. This is basically the standard way to represent the phase "
                           "of an orbital which controls which parts of an atom are accepting bonds at any given time.<br><br>"

                           "There is nothing more real or more imaginary about either orbital type. Any axial alignment is just from the equation and from the way the "
                           "spherical unit coordinate system is defined. There is nothing special about any particular direction. Just rotate the orbital. Walk around "
                           "the atom. Tilt your head at the screen. Many orbitals are the same shape and equally valid in any direction. The real knowledge to be gained "
                           "from this is how many unique (orthogonal) orbitals can be made for that specific energy level for bonding. And to get really really real, "
                           "these orbitals are not actually seen in real life at all, at least not in the way you are probably thinking. Again, they are not tangible. "
                           "They are probability maps. You can do some tricks with a fancy microscope and particle scattering and end up with the equivalent of a long "
                           "exposure image that shows you these orbitals, but from moment to moment, you will not see these beautiful shapes. I'm sorry to hurt you like "
                           "this. It's like finding out that the pole rotates.<br><br>"

                           "Anyways, electrons are somewhere in an orbital that has not decided on a shape yet. Until then, it is in superposition which is, to put it "
                           "simply, everywhere and nowhere at the same time. Or rather, the electrons have many positions they could be at, but you’ll never really know "
                           "where. Move over Schrodinger's cat, <i>psst psst</i> (that’s a spray bottle), and make way for an actually good analogy for superposition. "
                           "Superposition is kind of like playing hide and seek, and the hider can secretly move from one place to the next without being seen. Let’s say "
                           "the hider is in superposition among 5 hiding spots in a home. You know someone can’t be in 5 spots at the same time, but to play this game, "
                           "you actually have to act like they are. Additionally, you can also think of each room as being in a superposition between the states of being "
                           "occupied or empty. You go to spot one and observe the room’s 'state'. Is it empty or not? The state of the room is empty this time. "
                           "Equivalently, you can verify the state of the hider in that moment to be NOT in location 1. You go to location two and check. The state of "
                           "this room is also empty. You go to the third location, and the hider has taken an opportunity to sneak to location two, leaving the state of "
                           "location 3 to also be verified as empty. You are omniscient and want to <s>get on with this analogy</s> end the game, so you check location "
                           "two again and get a different result than last time. The state of the room is occupied. The state of the hider is within room two. With a lot "
                           "more quantum strangeness and math magic, this is basically what superposition is.<br><br>"

                           "I need to come clean about something... quantum mechanics is tough, and I've had to simplify some things to make this explanation accessible "
                           "to curious folks of all knowledge levels. So, I apologize for not getting into the high-level details of the topic, but shoulders of giants, "
                           "you know? I would love to share more with you, but at that point, I should just make a book. The point of this project is for you to see some "
                           "really cool shapes and lure you into the trap of a physics degree. If you don't want to end up as a physics student then <s>what are you doing "
                           "here? Leave! Get out! Shoo! Shoo!</s> I highly recommend that you do NOT look at these mind blowing orbitals: R|320>, R|431>, R|423>, and C|433> "
                           "(Focus on any specific color, and you have the nuclear symbol! What a fun coincidence‽) But seriously, I hope you enjoy this, and if you know "
                           "more quantum mechanics than the average person and dislike the oversimplifications, forgive me my transgressions. And if you think you "
                           "understand quantum mechanics, you don't!"}

        for tab_name, content_text in help_content.items():
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)

            text_area = QTextEdit()
            text_area.setReadOnly(True)

            text_area.setStyleSheet("QTextEdit { font-size: 12pt; }")

            text_area.setHtml(content_text)

            tab_layout.addWidget(text_area)
            self.tabs.addTab(tab, tab_name)

        layout.addWidget(self.tabs)

def open_help_menu(app):
    if not getattr(app, 'help_manager', None):
        app.unfreeze()
        app.help_manager = HelpMenu(parent=app.native)
        app.freeze()

    if not app.help_manager.isVisible():
        app.help_manager.show()
    else:
        app.help_manager.raise_()
        app.help_manager.activateWindow()
