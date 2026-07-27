import numpy as np
from skimage import measure
from vispy import scene
import quantum_math

def get_psi(n, l, m, basis, r, theta, phi):
    R = quantum_math.RADIAL_FUNCTIONS[(n, l)](r)
    A = quantum_math.BASE_EQUATIONS[(l, abs(m))](theta)

    if basis == "real":
        psi = R * A * np.cos(m * phi)
    elif basis == "imag":
        psi = R * A * (np.sin(m * phi) * 1j)
    else:
        psi = R * A * np.exp(1j * m * phi)

    prob = np.abs(psi) ** 2
    return psi, prob

def phase_to_color(angles, alpha=1.0):
    hue = (angles + np.pi) / (2 * np.pi)
    R_c = np.clip(np.abs(hue * 6.0 - 3.0) - 1.0, 0.0, 1.0)
    G_c = np.clip(2.0 - np.abs(hue * 6.0 - 2.0), 0.0, 1.0)
    B_c = np.clip(2.0 - np.abs(hue * 6.0 - 4.0), 0.0, 1.0)
    return np.column_stack((R_c, G_c, B_c, np.full(len(R_c), alpha)))

def apply_colors(angles, basis, pos_color, neg_color, alpha=1.0):
    if basis in ["real", "imag"]:
        if basis == "imag":
            is_pos = angles > 0
        else:
            is_pos = np.abs(angles) < (np.pi / 2)

        colors = np.empty((len(angles), 4))
        colors[is_pos] = pos_color
        colors[~is_pos] = neg_color
        # Enforce target alpha on base hex colors safely
        colors[:, 3] = alpha
        return colors
    else:
        return phase_to_color(angles, alpha)

def isosurfaces(n, l, m, basis, pos_color, neg_color, mask=None):
    grid_size = 100
    bounds = 10.0 + (n ** 2 * 2.5)

    if l == 0 and n > 1:
        isovalue_pct = 0.001
    else:
        isovalue_pct = {1: 0.05, 2: 0.05, 3: 0.05, 4: 0.02}.get(n, 0.05)

    u = np.linspace(-1.0, 1.0, grid_size)
    power = 3.0
    u_scaled = np.sign(u) * (np.abs(u) ** power)

    x = u_scaled * bounds
    y = u_scaled * bounds
    z = u_scaled * bounds

    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

    r = np.sqrt(X ** 2 + Y ** 2 + Z ** 2)
    r[r == 0] = 1e-10
    theta = np.arccos(Z / r)
    phi = np.arctan2(Y, X)

    psi, prob = get_psi(n, l, m, basis, r, theta, phi)

    if basis == "real":
        F = np.real(psi)
    elif basis == "imag":
        F = np.imag(psi)
    else:
        F = np.real(psi * np.exp(-1j * m * phi))

    max_F = np.max(np.abs(F))
    threshold = 1.0 if max_F < 1e-10 else max_F * np.sqrt(isovalue_pct)

    F_pos = np.where(F > 0, -F, 0.0)
    F_neg = np.where(F < 0, F, 0.0)

    if mask is not None:
        F_pos = np.where(mask, F_pos, 0.0)
        F_neg = np.where(mask, F_neg, 0.0)

    # Replaced vestigial material conditionals with standard transparent variables
    mesh_alpha = 0.5
    mesh_shading = 'smooth'

    pos_mesh_list = []
    neg_mesh_list = []

    for i, field in enumerate([F_pos, F_neg]):
        try:
            verts, faces, _, _ = measure.marching_cubes(field, level=-threshold)
            if len(verts) > 0:
                u_verts = (verts / (grid_size - 1)) * 2.0 - 1.0
                verts_real = np.sign(u_verts) * (np.abs(u_verts) ** power) * bounds
                idx = np.clip(np.round(verts).astype(int), 0, grid_size - 1)

                if len(faces) == 0:
                    continue

                angles = np.angle(psi[idx[:, 0], idx[:, 1], idx[:, 2]])
                colors = apply_colors(angles, basis, pos_color, neg_color, alpha=mesh_alpha)

                mesh = scene.visuals.Mesh(vertices=verts_real, faces=faces,
                                          vertex_colors=colors, shading=mesh_shading)

                radius = np.max(np.linalg.norm(verts_real, axis=1))

                # Split logic based on the enumerate index
                if i == 0:
                    pos_mesh_list.append((radius, mesh))
                else:
                    neg_mesh_list.append((radius, mesh))
        except (RuntimeError, ValueError):
            pass

    pos_mesh_list.sort(key=lambda x: x[0])
    neg_mesh_list.sort(key=lambda x: x[0])

    return [m[1] for m in pos_mesh_list], [m[1] for m in neg_mesh_list]

def point_cloud(n, l, m, basis, pos_color, neg_color):
    num_points = 2000 * n
    sample_pool = num_points * 10
    bounds = 10.0 + (n ** 2 * 2.5)

    r = np.random.rand(sample_pool) * bounds
    theta = np.arccos(1 - 2 * np.random.rand(sample_pool))
    phi = 2 * np.pi * np.random.rand(sample_pool)

    psi, prob = get_psi(n, l, m, basis, r, theta, phi)

    if l == 0 and n > 1:
        isovalue_pct = 0.0011
    else:
        isovalue_pct = {1: 0.05, 2: 0.05, 3: 0.05, 4: 0.02}.get(n, 0.05)

    max_prob = np.max(prob)
    threshold = 1.0 if max_prob < 1e-10 else max_prob * isovalue_pct

    density = prob.copy()
    density[prob < threshold] = 0.0
    sum_density = np.sum(density)

    if sum_density == 0:
        return [
            {"pos": np.empty((0, 3)), "face_color": 'white', "edge_width": 0, "size": 1},
            {"pos": np.empty((0, 3)), "face_color": 'white', "edge_width": 0, "size": 1}
        ]

    probs = density / sum_density
    non_zero_count = np.count_nonzero(probs)
    actual_num_points = min(num_points, non_zero_count)

    if actual_num_points == 0:
        return [
            {"pos": np.empty((0, 3)), "face_color": 'white', "edge_width": 0, "size": 1},
            {"pos": np.empty((0, 3)), "face_color": 'white', "edge_width": 0, "size": 1}
        ]

    chosen_idx = np.random.choice(sample_pool, size=actual_num_points, p=probs, replace=False)

    r_c = r[chosen_idx]
    theta_c = theta[chosen_idx]
    phi_c = phi[chosen_idx]
    psi_c = psi[chosen_idx]

    x = r_c * np.sin(theta_c) * np.cos(phi_c)
    y = r_c * np.sin(theta_c) * np.sin(phi_c)
    z = r_c * np.cos(theta_c)
    valid_pts = np.vstack((x, y, z)).T

    # Hardcoded standard point cloud alpha
    pt_alpha = 1.0
    angles = np.angle(psi_c)
    point_colors = apply_colors(angles, basis, pos_color, neg_color, alpha=pt_alpha)

    return [
        {"pos": valid_pts, "face_color": point_colors, "edge_width": 0, "size": 1},
        {"pos": np.empty((0, 3)), "face_color": 'white', "edge_width": 0, "size": 1}
    ]

def nodes(n, l, m, basis, scene_view, node_visuals, node_color):
    lookup_basis = "imag" if basis == "comp" else basis
    entry = (n, l, abs(m), lookup_basis)
    node_data = quantum_math.NODES.get(entry, {'radial': [], 'planar': [], 'conical': []})

    visual_scale = 8.0 + (n * 6.0)
    node_scale = visual_scale * 1.25

    for radius in node_data.get('radial', []):
        sphere = scene.visuals.Sphere(radius=radius, color=node_color,
                                      edge_color=node_color, parent=scene_view)
        node_visuals.append(sphere)

    s = node_scale
    p_verts = np.array([[-s, -s, 0], [s, -s, 0], [s, s, 0], [-s, s, 0]], dtype=np.float32)
    p_faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int32)

    # Do not show planar nodes for complex orbitals when m is not 0
    show_planar_nodes = not (basis == 'comp' and m != 0)

    if show_planar_nodes:
        for normal in node_data.get('planar', []):
            normal = np.array(normal, dtype=np.float32)
            plane = scene.visuals.Mesh(vertices=p_verts, faces=p_faces,
                                       color=node_color, parent=scene_view)

            plane.transform = scene.transforms.MatrixTransform()
            if abs(normal[2]) < 0.1:
                plane.transform.rotate(90, (0, 1, 0))
                angle_z = np.degrees(np.arctan2(normal[1], normal[0]))
                plane.transform.rotate(angle_z, (0, 0, 1))
            elif normal[2] < 0:
                plane.transform.rotate(180, (1, 0, 0))
            node_visuals.append(plane)

    for cot_sq in node_data.get('conical', []):
        h_val = node_scale
        r_val = h_val / np.sqrt(cot_sq)

        slices_count = 32
        angles = np.linspace(0, 2 * np.pi, slices_count)
        c_verts = [[0, 0, 0]] + [[r_val * np.cos(a), r_val * np.sin(a), h_val] for a in angles]
        c_verts = np.array(c_verts, dtype=np.float32)
        c_faces = np.array([[0, i, i + 1] for i in range(1, slices_count)] + [[0, slices_count, 1]], dtype=np.int32)

        for direction in [1, -1]:
            cone = scene.visuals.Mesh(vertices=c_verts, faces=c_faces,
                                      color=node_color, parent=scene_view)

            cone.transform = scene.transforms.MatrixTransform()
            if direction == -1:
                cone.transform.rotate(180, (1, 0, 0))
            node_visuals.append(cone)
