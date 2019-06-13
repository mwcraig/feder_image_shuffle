"""
Normalize names of FITS files for feder.
"""
from pathlib import Path

p = Path('.')

fits = list(p.glob('*.fit')) + list(p.glob('*.fts'))


for f in fits:
    # Replace spaces with dash
    new_name = str(f).replace(' ', '-')

    # Rename .fts to .fit
    new_name = new_name.replace('.fts', '.fit')

    # Actually rename the file
    f.rename(new_name)
