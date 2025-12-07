"""import numpy as np
import uproot
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import os

# Carica le coincidenze
coinc = uproot.open("data/output/posvalidation/coincidences_full.root")["Coincidences"]
x1 = coinc["globalPosX1"].array(library="np")
y1 = coinc["globalPosY1"].array(library="np")
x2 = coinc["globalPosX2"].array(library="np")
y2 = coinc["globalPosY2"].array(library="np")

print(f"Loaded {len(x1)} coincidences")

# Crea immagine per accumulare le LOR
image_size = 512
fov = 450
image = np.zeros((image_size, image_size))
scale = image_size / (2 * fov)
center = image_size // 2

print("Drawing LORs...")
n_points = 300
all_ix = []
all_iy = []
for i in range(len(x1)):
    t = np.linspace(0, 1, n_points)
    x = x1[i] + t * (x2[i] - x1[i])
    y = y1[i] + t * (y2[i] - y1[i])
    ix = (center + x * scale).astype(int)
    iy = (center + y * scale).astype(int)
    # Mask valid indices
    mask = (ix >= 0) & (ix < image_size) & (iy >= 0) & (iy < image_size)
    all_ix.append(ix[mask])
    all_iy.append(iy[mask])
# Concatenate all indices for both all_ix and all_iy
all_ix = np.concatenate(all_ix)
all_iy = np.concatenate(all_iy)
# Accumulate LORs and normalize image
np.add.at(image, (all_iy, all_ix), 1)
# Rimuovi background
background = np.percentile(image, 60)
image = image - background
image = np.maximum(image, 0)

# Esalta i picchi (le sovrapposizioni)
image = np.power(image, 0.5)

# Normalizza
image = image / image.max()

pet_colormap_colors = ['black', 'darkblue', 'blue', 'red', 'orange', 'yellow']
cmap = LinearSegmentedColormap.from_list('pet_cmap', pet_colormap_colors, N=256)
fig, ax = plt.subplots()
ax.set_facecolor('black')

im = ax.imshow(image, cmap=cmap, origin='lower',
               extent=[-fov, fov, -fov, fov])

# Cerchio del ring detector
theta = np.linspace(0, 2*np.pi, 100)
ring_radius = 391.5
ax.plot(ring_radius * np.cos(theta), ring_radius * np.sin(theta), 
        'white', linewidth=1, linestyle='--', alpha=0.5)

ax.set_xlabel('X (mm)', color='white')
ax.set_ylabel('Y (mm)', color='white')
ax.set_title('PET LOR Visualization - Full Ring', color='white')
ax.tick_params(colors='white')

cbar = plt.colorbar(im, ax=ax, label='Overlap Intensity')
cbar.ax.yaxis.set_tick_params(color='white')
cbar.ax.yaxis.label.set_color('white')
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

#plt.savefig("data/output/posvalidation/LOR_visualization1.png", dpi=150, bbox_inches='tight', facecolor='black')
# Nome file unico basato sul numero di coincidenze
n_coinc = len(x1)
output_name = f"data/output/posvalidation/LOR_{n_coinc}_coincidences.png"
plt.savefig(output_name, dpi=150, bbox_inches='tight', facecolor='black')
print(f"Saved: {output_name}")
# All output messages are in English for consistency
print(f"Saved: {output_name}") 
print(f"Salvato: {output_name}") 
"""
import numpy as np
import uproot
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


def plot_coincidences(coinc_file, output_file=None, title=None):
    """
    Genera visualizzazione LOR da file coincidenze.
    
    Parameters
    ----------
    coinc_file : str
        Percorso al file ROOT con coincidenze
    output_file : str, optional
        Percorso output immagine. Se None, genera nome automatico.
    title : str, optional
        Titolo del plot
        
    Returns
    -------
    str
        Percorso del file salvato
    """
    # Carica coincidenze
    coinc = uproot.open(coinc_file)["Coincidences"]
    x1 = coinc["globalPosX1"].array(library="np")
    y1 = coinc["globalPosY1"].array(library="np")
    x2 = coinc["globalPosX2"].array(library="np")
    y2 = coinc["globalPosY2"].array(library="np")
    
    n_coinc = len(x1)
    print(f"  Loaded {n_coinc} coincidences")
    
    # Nome file automatico se non specificato
    if output_file is None:
        base = coinc_file.replace('.root', '')
        output_file = f"{base}_{n_coinc}coinc.png"
    
    # Titolo automatico se non specificato
    if title is None:
        title = f"PET LOR Visualization - {n_coinc} coincidences"
    
    # Crea immagine
    image_size = 512
    fov = 450
    image = np.zeros((image_size, image_size))
    scale = image_size / (2 * fov)
    center = image_size // 2
    
    print("  Drawing LORs...")
    n_points = 300
    for i in range(len(x1)):
        for t in np.linspace(0, 1, n_points):
            x = x1[i] + t * (x2[i] - x1[i])
            y = y1[i] + t * (y2[i] - y1[i])
            ix = int(center + x * scale)
            iy = int(center + y * scale)
            if 0 <= ix < image_size and 0 <= iy < image_size:
                image[iy, ix] += 1
    
    # Migliora contrasto
    background = np.percentile(image, 60)
    image = image - background
    image = np.maximum(image, 0)
    image = np.power(image, 0.5)
    if image.max() > 0:
        image = image / image.max()
    
    # Colormap
    colors = ['black', 'darkblue', 'blue', 'red', 'orange', 'yellow']
    cmap = LinearSegmentedColormap.from_list('pet_cmap', colors, N=256)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 10), facecolor='black')
    ax.set_facecolor('black')
    
    im = ax.imshow(image, cmap=cmap, origin='lower',
                   extent=[-fov, fov, -fov, fov])
    
    # Ring detector
    theta = np.linspace(0, 2*np.pi, 100)
    ring_radius = 391.5
    ax.plot(ring_radius * np.cos(theta), ring_radius * np.sin(theta), 
            'white', linewidth=1, linestyle='--', alpha=0.5)
    
    ax.set_xlabel('X (mm)', color='white')
    ax.set_ylabel('Y (mm)', color='white')
    ax.set_title(title, color='white')
    ax.tick_params(colors='white')
    
    cbar = plt.colorbar(im, ax=ax, label='Intensity')
    cbar.ax.yaxis.set_tick_params(color='white')
    cbar.ax.yaxis.label.set_color('white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    ax.set_aspect('equal')
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()
    
    print(f"  Saved: {output_file}")
    return output_file


# Esecuzione standalone
if __name__ == "__main__":
    plot_coincidences("data/output/posvalidation/coincidences_full.root")
