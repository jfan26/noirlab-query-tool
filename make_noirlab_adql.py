# make_noirlab_adql.py

import os

def generate_adql_scripts(output_dir="adql_queries"):
    ra_min, ra_max = 75, 300
    dec_start, dec_end = 32.0, 85.0
    dec_step = 0.5
    snr_z_threshold = 2.0

    adql_template = """
SELECT ra, dec, dered_mag_g, dered_mag_r, dered_mag_z, type, 
       snr_g, snr_r, snr_z, maskbits, mag_w1, mag_w2, snr_w1, snr_w2
FROM ls_dr10.tractor
WHERE ra BETWEEN {ra_min} AND {ra_max}
  AND dec BETWEEN {dec_min} AND {dec_max}
  AND snr_z > {snr_z}
"""

    os.makedirs(output_dir, exist_ok=True)

    dec_min = dec_start
    count = 0
    while dec_min < dec_end:
        dec_max = round(dec_min + dec_step, 1)
        query = adql_template.format(
            ra_min=ra_min,
            ra_max=ra_max,
            dec_min=dec_min,
            dec_max=dec_max,
            snr_z=snr_z_threshold
        )
        filename = f"query_dec_{dec_min:.1f}_to_{dec_max:.1f}.adql"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            f.write(query.strip() + "\n")
        count += 1
        dec_min = dec_max

    print(f"[OK] Saved {count} ADQL scripts to '{output_dir}/'")

# Run
if __name__ == "__main__":
    generate_adql_scripts()
