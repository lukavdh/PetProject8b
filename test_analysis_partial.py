import numpy as np
import uproot
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter

# Carica le coincidenze PARTIAL RING
coinc = uproot.open("data/output/posvalidation/coincidences_partial.root")["Coincidences"]
x1 = coinc["globalPosX1"].array(library="np")
y1 = coinc["globalPosY1"].array(library="np")
x2 = coinc["globalPosX2"].array(library="np")
y2 = coinc["globalPosY2"].array(library="np")

print(f"Loaded {len(x1)} coincidences (Partial Ring)")

# Crea immagine
image_size = 512
fov = 450
image = np.zeros((image_size, image_size))
scale = image_size / (2 * fov)
center = image_size // 2

print("Drawing LORs...")
n_points = 300
for i in range(len(x1)):
    for t in np.linspace(0, 1, n_points):
        x = x1[i] + t * (x2[i] - x1[i])
        y = y1[i] + t * (y2[i] - y1[i])
        ix = int(center + x * scale)
        iy = int(center + y * scale)
        if 0 <= ix < image_size and 0 <= iy < image_size:
            image[iy, ix] += 1

# Rimuovi background e aumenta contrasto
background = np.percentile(image, 60)
image = image - background
image = np.maximum(image, 0)
image = np.power(image, 0.5)
image = image / image.max()

# Colormap
colors = ['black', 'darkblue', 'blue', 'red', 'orange', 'yellow']
cmap = LinearSegmentedColormap.from_list('pet_cmap', colors, N=256)

# Plot
fig, ax = plt.subplots(figsize=(10, 10), facecolor='black')
ax.set_facecolor('black')

im = ax.imshow(image, cmap=cmap, origin='lower',
               extent=[-fov, fov, -fov, fov])

# Cerchio del ring detector
theta = np.linspace(0, 2*np.pi, 100)
ring_radius = 391.5
ax.plot(ring_radius * np.cos(theta), ring_radius * np.sin(theta), 
        'white', linewidth=1, linestyle='--', alpha=0.5)

# Marca posizione dei 2 moduli
ax.plot([-391.5], [0], 's', color='cyan', markersize=15, label='Module 1')
ax.plot([391.5], [0], 's', color='cyan', markersize=15, label='Module 2')

# Marca le sorgenti
ax.plot(-50, 50, 'o', color='lime', markersize=12, markerfacecolor='none', 
        markeredgewidth=2, label='Source 1')
ax.plot(50, -50, 'o', color='lime', markersize=12, markerfacecolor='none',
        markeredgewidth=2, label='Source 2')

ax.set_xlabel('X (mm)', color='white')
ax.set_ylabel('Y (mm)', color='white')
ax.set_title('PET LOR Visualization - Partial Ring (2 modules)', color='white')
ax.tick_params(colors='white')
ax.legend(loc='upper right', facecolor='black', edgecolor='white', labelcolor='white')

cbar = plt.colorbar(im, ax=ax, label='Overlap Intensity')
cbar.ax.yaxis.set_tick_params(color='white')
cbar.ax.yaxis.label.set_color('white')
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

ax.set_aspect('equal')
plt.savefig("data/output/posvalidation/LOR_partial_ring.png", 
            dpi=150, bbox_inches='tight', facecolor='black')
print("Salvato: LOR_partial_ring.png")

