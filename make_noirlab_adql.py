# make_noirlab_adql.py

import os
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

# ADQL query parameters
RA_MIN_BASE = 0
RA_MAX_BASE = 360
DEC_START = -90.0
DEC_END = 90.0
DEC_STEP = 0.5

# Galactic latitude parameters
GALACTIC_LAT = None  # Set to "north", "south", or None
MW_DISK_LAT1 = 15.0   # Northern boundary of the Milky Way (degrees) - DO NOT CHANGE
MW_DISK_LAT2 = -15.0  # Southern boundary of the Milky Way (degrees) - DO NOT CHANGE

ADQL_TEMPLATE = """
SELECT ra, dec, dered_mag_g, dered_mag_r, dered_mag_i, dered_mag_z, type, snr_g, snr_r, snr_i, snr_z, 
    maskbits, mag_w1, mag_w2, snr_w1, snr_w2, ebv, fitbits, parallax, parallax_ivar, 
    psfdepth_g, psfdepth_r, psfdepth_i, psfdepth_z, psfdepth_w1, psfdepth_w2, 
    psfsize_g, psfsize_r, psfsize_i, psfsize_z
FROM ls_dr10.tractor
WHERE ra BETWEEN {ra_min} AND {ra_max}
  AND dec BETWEEN {dec_min} AND {dec_max}
  AND (snr_z > 1.5 OR snr_i > 1.5)
"""

def galactic_to_equatorial(l_deg, b_deg):
    """Convert Galactic to Equatorial coordinates."""
    gal = SkyCoord(l=np.asarray(l_deg) * u.deg, b=np.asarray(b_deg) * u.deg, frame="galactic")
    eq = gal.icrs
    return eq.ra.deg, eq.dec.deg

def icrs_to_galactic_b(ra_deg, dec_deg):
    """Convert Equatorial to Galactic latitude."""
    icrs = SkyCoord(ra=np.asarray(ra_deg) * u.deg, dec=np.asarray(dec_deg) * u.deg, frame="icrs")
    return icrs.galactic.b.deg

def find_ra_at_dec_crossing(dec_target):
    """Find RA values where a given Galactic latitude crosses a specific declination.
    Returns both left and right crossing points if they exist."""
    l_vals = np.linspace(0.0, 360.0, 10000)
    if GALACTIC_LAT == "north":
        b_vals = np.full_like(l_vals, MW_DISK_LAT1, dtype=float)
    elif GALACTIC_LAT == "south":
        b_vals = np.full_like(l_vals, MW_DISK_LAT2, dtype=float)
    else:
        return None, None
    
    ra_deg_line, dec_deg_line = galactic_to_equatorial(l_vals, b_vals)
    
    # Find where the line crosses dec_target
    y = dec_deg_line - dec_target
    crossings = []
    for i in range(len(y) - 1):
        if y[i] * y[i+1] <= 0:  # Sign change indicates crossing
            if y[i] == y[i+1]:
                continue
            t = (-y[i]) / (y[i+1] - y[i])
            if 0.0 <= t <= 1.0:
                ra_crossing = ra_deg_line[i] + t * (ra_deg_line[i+1] - ra_deg_line[i])
                crossings.append(ra_crossing % 360.0)
    
    if len(crossings) >= 2:
        # Return both boundaries
        return sorted(crossings)[0], sorted(crossings)[1]
    elif len(crossings) == 1:
        # Only one crossing found
        return crossings[0], None
    else:
        return None, None

def generate_adql_scripts(output_dir="adql_queries"):
    # Base RA range
    ra_min_base, ra_max_base = RA_MIN_BASE, RA_MAX_BASE

    os.makedirs(output_dir, exist_ok=True)

    dec_min = DEC_START
    count = 0
    while dec_min < DEC_END:
        dec_max = round(dec_min + DEC_STEP, 1)
        
        # Adjust RA limits based on galactic latitude if specified
        ra_min, ra_max = ra_min_base, ra_max_base
        if GALACTIC_LAT is not None:
            ra_boundary_left, ra_boundary_right = find_ra_at_dec_crossing(dec_min)
            
            if ra_boundary_left is not None and ra_boundary_right is not None:
                # Both boundaries found - apply the filter
                if GALACTIC_LAT == "north":
                    # Keep RA values between the two boundaries (north of the plane)
                    ra_min = max(ra_min_base, ra_boundary_left)
                    ra_max = min(ra_max_base, ra_boundary_right)
                elif GALACTIC_LAT == "south":
                    # Keep RA values outside the boundaries (south of the plane)
                    # For now, just constrain to left side; could also handle right side
                    ra_max = min(ra_max_base, ra_boundary_left)
            elif ra_boundary_left is not None:
                # Only one boundary found - declination band is entirely on one side
                # Check a test point to see if it's north or south of the boundary
                test_ra = (ra_min_base + ra_max_base) / 2
                test_b = icrs_to_galactic_b(test_ra, dec_min)
                
                is_north = test_b > MW_DISK_LAT1
                
                if GALACTIC_LAT == "north" and not is_north:
                    # Want north but entire band is south - skip this declination
                    ra_min, ra_max = ra_min_base, ra_min_base  # Empty range
                elif GALACTIC_LAT == "south" and is_north:
                    # Want south but entire band is north - skip this declination
                    ra_min, ra_max = ra_min_base, ra_min_base  # Empty range
                # Otherwise entire band matches filter, keep full range
        
        # Skip if RA range is empty (entire band excluded by galactic filter)
        if ra_min >= ra_max:
            dec_min = dec_max
            continue
        
        query = ADQL_TEMPLATE.format(
            ra_min=ra_min,
            ra_max=ra_max,
            dec_min=dec_min,
            dec_max=dec_max,
            snr_z=SNR_Z_THRESHOLD
        )
        
        # Generate filename with RA range and galactic latitude if applicable
        if GALACTIC_LAT is not None:
            gal_label = "galN" if GALACTIC_LAT == "north" else "galS"
            filename = f"{gal_label}_r{ra_min:.2f}_{ra_max:.2f}_d{dec_min:.1f}_{dec_max:.1f}.adql"
        else:
            filename = f"r{ra_min:.2f}_{ra_max:.2f}_d{dec_min:.1f}_{dec_max:.1f}.adql"
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            f.write(query.strip() + "\n")
        count += 1
        dec_min = dec_max

    print(f"[OK] Saved {count} ADQL scripts to '{output_dir}/'")

# Run
if __name__ == "__main__":
    generate_adql_scripts()
