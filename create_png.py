import rasterio
import numpy as np

from matplotlib.colors import ListedColormap
import os
import matplotlib.pyplot as plt

BUFFER = 8
INPUT_FILE = "data/jay_peak_region_{BUFFER}.tif"
DOWNSAMPLE = 60
MIN_ELEVATION_M = 400
CONTOUR_INTERVAL_M = 30
SMOOTH_SIGMA = 3.

COLOR_THRESHOLD_1 = 300  # Orange clair
COLOR_THRESHOLD_2 = 800  # Orange moyen
COLOR_THRESHOLD_3 = 1000  # Orange foncé (sommet)

OUTPUT_PNG = "jay_peak_map.png"

def load_and_downsample():
    with rasterio.open(INPUT_FILE) as src:
        print(f"Opening: {INPUT_FILE}")
        print(f"  Original size: {src.height} x {src.width} pixels")
        
        new_height = src.height // DOWNSAMPLE
        new_width = src.width // DOWNSAMPLE
        new_res = src.res[0] * DOWNSAMPLE
        print(f"  Downsample: {DOWNSAMPLE}x → resolution {new_res:.1f}m")
        print(f"  Final size: {new_height} x {new_width} pixels")
        
        elevation = src.read(
            1,
            out_shape=(new_height, new_width),
            resampling=rasterio.enums.Resampling.average,
            masked=True
        )
        
        if src.nodata is not None:
            elevation = np.ma.masked_equal(elevation, src.nodata)
        
        elevation = np.ma.masked_less(elevation, -100)
        
        print(f"  Before MIN_ELEVATION filter: {np.nanmin(elevation):.0f}m - {np.nanmax(elevation):.0f}m")
        
        elevation = np.ma.masked_where(elevation < MIN_ELEVATION_M, elevation)
        valid = elevation[~elevation.mask]
        print(f"  After MIN_ELEVATION filter: {valid.min():.0f}m - {valid.max():.0f}m")
        
        transform = src.transform * src.transform.scale(DOWNSAMPLE)
        
        x_coords = np.arange(new_width) * transform[0] + transform[2]
        y_coords = np.arange(new_height) * transform[4] + transform[5]
        
        return elevation, x_coords, y_coords
    

def create_matplotlib_map(elevation, x, y,
                              color_levels=[400, 600, 800, 1000, 1200],
                              colors=['#E8D5B7', '#D9BC8C', '#C9A66B', '#B8934F', '#A67C3B'],
                              min_contour_elev=600) -> plt.Figure:
    
    plt.rcParams['font.family'] = 'Futura'
    plt.rcParams['font.size'] = 24
    
    min_elev = np.nanmin(elevation)
    max_elev = np.nanmax(elevation)
    
    contour_levels = np.arange(
        np.ceil(min_elev / CONTOUR_INTERVAL_M) * CONTOUR_INTERVAL_M,
        np.floor(max_elev / CONTOUR_INTERVAL_M) * CONTOUR_INTERVAL_M + CONTOUR_INTERVAL_M,
        CONTOUR_INTERVAL_M
    )
    contour_levels = contour_levels[contour_levels >= min_contour_elev]
    
    fig, ax = plt.subplots(figsize=(24, 36), dpi=650)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    
    X, Y = np.meshgrid(x, y)
    
    color_boundaries = color_levels + [max_elev + 100]
    
    cmap = ListedColormap(colors)
    
    ax.contourf(X, Y, elevation, levels=color_boundaries, 
                colors=colors, alpha=0.5, antialiased=True, extend='neither')
    
    levels_major = contour_levels[::3]
    levels_normal = contour_levels[~np.isin(contour_levels, levels_major)]
    
    ax.contour(X, Y, elevation, levels=levels_normal, 
               colors='#8B7355', linewidths=1.2, alpha=0.5, zorder=1)
    
    contours_major = ax.contour(X, Y, elevation, levels=levels_major, 
                                 colors='#523C22', linewidths=1.5, alpha=0.85, zorder=2)
    
    ax.contour(X, Y, elevation, levels=[contour_levels[-1]], 
               colors='#523C22', linewidths=1.2, alpha=1.0, zorder=3)
    
    ax.clabel(contours_major, inline=True, fmt='%d m', 
              colors='#3D2817', fontsize=12, zorder=10)
    
    from scipy.ndimage import maximum_filter, generate_binary_structure
    
    neighborhood = generate_binary_structure(2, 2)
    local_max = maximum_filter(elevation.filled(-9999), footprint=neighborhood) == elevation.filled(-9999)
    local_max = local_max & (elevation > max_elev - 100)
    
    peak_indices = np.where(local_max)
    peak_coords = []
    
    for i in range(len(peak_indices[0])):
        py = peak_indices[0][i]
        px = peak_indices[1][i]
        peak_x = X[py, px]
        peak_y = Y[py, px]
        
        too_close = False
        for existing_x, existing_y in peak_coords:
            distance = np.sqrt((peak_x - existing_x)**2 + (peak_y - existing_y)**2)
            if distance < 500:
                too_close = True
                break
        
        if not too_close:
            peak_coords.append((peak_x, peak_y))
            ax.plot(peak_x, peak_y, '+', color='#523C22', 
                    markersize=24, markeredgewidth=1.7, alpha=0.8, zorder=11)
    
    ax.axis('off')
    ax.set_aspect('equal')

    plt.tight_layout()
    return fig


def save_outputs(fig) -> None:    
    print(f"PNG: {OUTPUT_PNG}")
 
    fig.write_image(OUTPUT_PNG, width=2400, height=2000, scale=2)
    print(f"{os.path.getsize(OUTPUT_PNG) / 1e6:.1f} MB")
    

if __name__ == '__main__':
    elevation, x, y = load_and_downsample()
    fig = create_matplotlib_map(
        elevation, x, y,
        color_levels=[780,810, 840,870,930, 990, 1110],
        colors=["#F3EBDD", 
        "#E8D6B8",
        "#DDBE8E",
        "#D39E5E",
        "#C77833",
        "#B04A1F",
        "#7E2A1E"  ]
    )
    save_outputs(fig)