import numpy as np

MAX_n = 4

#Radial Function R_nl -> (n, l)
RADIAL_FUNCTIONS = {
(1, 0): lambda r: 2.0 * np.exp(-r),

(2, 0): lambda r: 0.353553 * (2.0 - r) * np.exp(-0.5 * r),
(2, 1): lambda r: 0.204124 * r * np.exp(-0.5 * r),

(3, 0): lambda r: 0.0142556 * (27.0 - r * (18.0 - 2.0 * r)) * np.exp(-0.333333 * r),
(3, 1): lambda r: 0.0201604 * r * (6.0 - r) * np.exp(-0.333333 * r),
(3, 2): lambda r: 0.009016 * (r * r) * np.exp(-0.333333 * r),

(4, 0): lambda r: 0.00130208 * (192.0 - r * (144.0 - r * (24.0 - r))) * np.exp(-0.25 * r),
(4, 1): lambda r: 0.00100859 * (r * (80.0 - r * (20.0 - r))) * np.exp(-0.25 * r),
(4, 2): lambda r: 0.000582309 * ((12.0 - r) * r * r) * np.exp(-0.25 * r),
(4, 3): lambda r: 0.0002200923 * (r * r * r) * np.exp(-0.25 * r)}

#Angular Function Y_l^m -> (l, m)
BASE_EQUATIONS = {
(0, 0): lambda theta: 0.282095 * np.ones_like(theta),

(1, 0): lambda theta: 0.488603 * np.cos(theta),
(1, 1): lambda theta: -0.345494 * np.sin(theta),

(2, 0): lambda theta: 0.315392 * (3.0 * np.cos(theta) * np.cos(theta) - 1.0),
(2, 1): lambda theta: -0.772548 * np.sin(theta) * np.cos(theta),
(2, 2): lambda theta: 0.386274 * np.sin(theta) * np.sin(theta),

(3, 0): lambda theta: 0.373176 * (np.cos(theta) * (5.0 * np.cos(theta) * np.cos(theta) - 3.0)),
(3, 1): lambda theta: -0.32318 * np.sin(theta) * (5.0 * np.cos(theta) * np.cos(theta) - 1.0),
(3, 2): lambda theta: 1.02199 * np.sin(theta) * np.sin(theta) * np.cos(theta),
(3, 3): lambda theta: -0.417224 * np.sin(theta) * np.sin(theta)* np.sin(theta)}

# radial node: sphere, rho = radius, radius = [val]
# planar node: plane, ax+by+cz = 0, normal = [a, b, c]
# conical node: double cone, z^2 = (x^2 + y^2)*val, val = [cot^2(ang)]
NODES = {
    # s orbitals
    (2, 0, 0, 'real'): {'radial': [2.0], 'planar': [], 'conical': []},
    (3, 0, 0, 'real'): {'radial': [1.9, 7.1], 'planar': [], 'conical': []},
    (4, 0, 0, 'real'): {'radial': [1.87, 6.61, 15.52], 'planar': [], 'conical': []},

    # p orbitals
    (2, 1, 0, 'real'): {'radial': [], 'planar': [[0.0, 0.0, 1.0]], 'conical': []},
    (2, 1, 1, 'real'): {'radial': [], 'planar': [[1.0, 0.0, 0.0]], 'conical': []},
    (2, 1, 1, 'imag'): {'radial': [], 'planar': [[0.0, 1.0, 0.0]], 'conical': []},
    (3, 1, 0, 'real'): {'radial': [6.0], 'planar': [[0.0, 0.0, 1.0]], 'conical': []},
    (3, 1, 1, 'real'): {'radial': [6.0], 'planar': [[1.0, 0.0, 0.0]], 'conical': []},
    (3, 1, 1, 'imag'): {'radial': [6.0], 'planar': [[0.0, 1.0, 0.0]], 'conical': []},
    (4, 1, 0, 'real'): {'radial': [5.53, 14.47], 'planar': [[0.0, 0.0, 1.0]], 'conical': []},
    (4, 1, 1, 'real'): {'radial': [5.53, 14.47], 'planar': [[1.0, 0.0, 0.0]], 'conical': []},
    (4, 1, 1, 'imag'): {'radial': [5.53, 14.47], 'planar': [[0.0, 1.0, 0.0]], 'conical': []},

    # d orbitals
    (3, 2, 0, 'real'): {'radial': [], 'planar': [], 'conical': [0.5]},
    (3, 2, 1, 'real'): {'radial': [], 'planar': [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]], 'conical': []},
    (3, 2, 2, 'real'): {'radial': [], 'planar': [[1.0, 1.0, 0.0], [1.0, -1.0, 0.0]], 'conical': []},
    (3, 2, 1, 'imag'): {'radial': [], 'planar': [[0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], 'conical': []},
    (3, 2, 2, 'imag'): {'radial': [], 'planar': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], 'conical': []},
    (4, 2, 0, 'real'): {'radial': [12.0], 'planar': [], 'conical': [0.5]},
    (4, 2, 1, 'real'): {'radial': [12.0], 'planar': [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]], 'conical': []},
    (4, 2, 2, 'real'): {'radial': [12.0], 'planar': [[1.0, 1.0, 0.0], [1.0, -1.0, 0.0]], 'conical': []},
    (4, 2, 1, 'imag'): {'radial': [12.0], 'planar': [[0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], 'conical': []},
    (4, 2, 2, 'imag'): {'radial': [12.0], 'planar': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], 'conical': []},

    # f orbitals
    (4, 3, 0, 'real'): {'radial': [], 'planar': [[0.0, 0.0, 1.0]], 'conical': [1.5]},
    (4, 3, 1, 'real'): {'radial': [], 'planar': [[1.0, 0.0, 0.0]], 'conical': [0.25]},
    (4, 3, 2, 'real'): {'radial': [], 'planar': [[1.0, -1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 1.0]], 'conical': []},
    (4, 3, 3, 'real'): {'radial': [], 'planar': [[1.0, 0.0, 0.0], [0.5, 0.866, 0.0], [0.5, -0.866, 0.0]], 'conical': []},
    (4, 3, 1, 'imag'): {'radial': [], 'planar': [[0.0, 1.0, 0.0]], 'conical': [0.25]},
    (4, 3, 2, 'imag'): {'radial': [], 'planar': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], 'conical': []},
    (4, 3, 3, 'imag'): {'radial': [], 'planar': [[0.0, 1.0, 0.0], [0.866, 0.5, 0.0], [0.866, -0.5, 0.0]], 'conical': []}}

ORBITAL_NAMES = {
    (1, 0, 0, 'real'): "1s",
    (2, 0, 0, 'real'): "2s",
    (2, 1, 0, 'real'): "2pz",
    (2, 1, 1, 'real'): "2px",
    (2, 1, 1, 'imag'): "2py",
    (3, 0, 0, 'real'): "3s",
    (3, 1, 0, 'real'): "3pz",
    (3, 1, 1, 'real'): "3px",
    (3, 1, 1, 'imag'): "3py",
    (3, 2, 0, 'real'): "3dz²",
    (3, 2, 1, 'real'): "3dxz",
    (3, 2, 1, 'imag'): "3dyz",
    (3, 2, 2, 'real'): "3dx²-y²",
    (3, 2, 2, 'imag'): "3dxy",
    (4, 0, 0, 'real'): "4s",
    (4, 1, 0, 'real'): "4pz",
    (4, 1, 1, 'real'): "4px",
    (4, 1, 1, 'imag'): "4py",
    (4, 2, 0, 'real'): "4dz²",
    (4, 2, 1, 'real'): "4dxz",
    (4, 2, 1, 'imag'): "4dyz",
    (4, 2, 2, 'real'): "4dx²-y²",
    (4, 2, 2, 'imag'): "4dxy",
    (4, 3, 0, 'real'): "4fz³",
    (4, 3, 1, 'real'): "4fxz²",
    (4, 3, 1, 'imag'): "4fyz²",
    (4, 3, 2, 'real'): "4fz(x²-y²)",
    (4, 3, 2, 'imag'): "4fxyz",
    (4, 3, 3, 'real'): "4fx(x²-3y²)",
    (4, 3, 3, 'imag'): "4fy(3x²-y²)"}
