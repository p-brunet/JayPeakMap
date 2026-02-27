
import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer

S3_URL = "/vsicurl/https://s3.us-east-2.amazonaws.com/vtopendata-prd/_Other/Projects/2023_Lidar/PreliminaryData/Northern/Northern_2023_35cm_DSMFR.tif"
BUFFER_KM = 8
OUTPUT_FILE = "data/jay_peak_region_{BUFFER_KM}.tif"

JAY_PEAK_LAT = 44.924384
JAY_PEAK_LON = -72.511729


def extract_jay_peak():
    

    with rasterio.open(S3_URL) as src:
        print("File opened")
        
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32145", always_xy=True)
        
        jay_x, jay_y = transformer.transform(JAY_PEAK_LON, JAY_PEAK_LAT)
        
        print("\nJAY PEAK:")
        print("  GPS: {JAY_PEAK_LAT}°N, {JAY_PEAK_LON}°W")
        print("  Vermont State Plane: X={jay_x:,.0f}, Y={jay_y:,.0f}")
        
        buffer_m = BUFFER_KM * 1000
        
        window = from_bounds(
            jay_x - buffer_m,
            jay_y - buffer_m,
            jay_x + buffer_m,
            jay_y + buffer_m,
            src.transform
        )
        
        print(f"\nEXTRACTION:")
        print(f"  Zone: {BUFFER_KM*2}km x {BUFFER_KM*2}km")
        print(f"  Window: {window.height} x {window.width} pixels")
        print(f"  Size: {window.height * window.width * 4 / 1e6:.1f} MB")
        
        print("Downloading...")
        data = src.read(1, window=window)
        
        transform = src.window_transform(window)
        profile = src.profile.copy()
        profile.update({
            'height': window.height,
            'width': window.width,
            'transform': transform,
            'BIGTIFF': 'YES' #This option is crucial for large files
        })
        
        with rasterio.open(OUTPUT_FILE, 'w', **profile) as dst:
            dst.write(data, 1)
        
        import os
        size_mb = os.path.getsize(OUTPUT_FILE) / 1e6
        
        print(f"\n{'='*60}")
        print("Done!")
        print(f"{'='*60}")
        print(f"File: {OUTPUT_FILE}")
        print(f"Size: {size_mb:.1f} MB")
        print(f"Elevation: {data.min():.1f}m - {data.max():.1f}m")
        
        print(f"\nSummit à {data.max():.1f}m !")
        

if __name__ == '__main__':
    extract_jay_peak()