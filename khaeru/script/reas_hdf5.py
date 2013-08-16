#!/usr/bin/env python3
"""Convert the REAS 2.1 database into a HDF5 file

This script converts the data from the "Country and Regional Tables" of
the Regional Emission inventory in ASia (REAS), version 2.1, from their
native text file format to a file containing HDF5 datasets.


REQUIREMENTS

The contents of the tables are provided at [1] as ZIP archive
containing directories and text files. The files must all be present in
the directory where this script is executed, i.e. not in their default
directory hierarchy.

The file `h5enum.py`, and the `h5py` module [2] and its dependencies
(including the HDF5 library and NumPy) are also required.


DETAILS

A file 'reas.h5' is produced.

The description of the table [2] gives the codes and definitions of
fuels and sectors for both combustion- and non-combustion emissions. The
actual data files have some errors; see the comments for `N_sc` and
`N_so` below.

1. http://www.nies.go.jp/REAS/
2. http://www.h5py.org/
2. http://www.nies.go.jp/REAS/REASv2.1%20TABLE/Brief%20description%20
   about%20table%20data%20v2.1.pdf

"""
import os

import h5py, numpy

from h5enum import create_enum_dataset


OUTPUT = 'reas.h5'

# shorthand references to the data file, and datasets for *c*ombustion, 
# n*o*n-combustion, and *t*otal emissions
df = None
dc = None
do = None
dt = None

# dimensions
p = set()  # pollutants
y = set()  # years
r = set()  # all regions and sub-regions

# minor cheating to avoid excess complexity in this code: pre-counted
# number of elements in these sets
# … +1 for SUB_TOTAL
# … +N for errors or inconsistencies as noted
N_f = 17+1     # combustion fuels
N_sc = 28+1+6  # combustion source sectors, including the erroneous extras:
               # - AGRICULT (unlisted, should probably be AGR_FORE)
               # - FISHING (should be AGR_FORE_FISH)
               # - FERTPROD (should be FERT_PROD)
               # - GASPROD (should be GAS_PROD)
               # - SMALLINCIN (should be SMALL_INCIN)
               # - WASTEINCIN (should be WASTE_INCIN)
N_so = 71+1+1  # non-combustion source sectors

# counters for adding elements to f, sc, so
counter = {'f': 0, 'sc': 0, 'so': 0}


def ds_lookup(ds, value, add=False):
  """Lookup *value* in *ds* and return an index
  
  The h5py.Dataset named *ds* in the variable `df` is searched for the
  index of the item *value*. If *value* is not present and *add* is
  False (default), any exception is allowed to propagate. If *add* is
  True, *value* is added as the last entry in *ds* and its index is
  returned.
  """
  try:
    return numpy.where(df[ds].value == value)[0][0]
  except Exception as e:
    if not add:
      raise e
    global counter
    df[ds][counter[ds]] = value
    print('Added {} to `{}` in index {}'.format(value, ds, counter[ds]))
    counter[ds] += 1
    return counter[ds] - 1


# file names look like: REASv2.1_NH3_2008_IND_TAMI.txt
#                   or: REASv2.1_PM2.5_2008_IND_TAMI.txt
chunk = [9, 3, 1, 4, 1, 8]
def fn_parts(fn):
  """Split the filename *fn* into chunks
  
  Returns a 3-tuple corresponding to the pollutant, year, and region.
  """
  chunk[1] = 5 if '_PM' in fn else 3
  pts = [fn[sum(chunk[:i]):sum(chunk[:i])+chunk[i]] for i in range(len(chunk))]
  return pts[1], pts[3], pts[5]


def HDF5_setup():
  """Initialize the HDF file to contain the data."""
  global df, dc, do, dt
  df = h5py.File(OUTPUT, 'w')
  # set up dimensions
  dt = h5py.special_dtype(vlen=str)
  df.create_dataset('p', (len(p),), dtype=dt)
  df['p'][:] = p
  df.create_dataset('y', (len(y),), dtype=dt)
  df['y'][:] = y
  df.create_dataset('r', (len(r),), dtype=dt)
  df['r'][:] = r
  # dimensions for source sectors and fuels — labels will be populated by
  # `ds_lookup`
  df.create_dataset('f', (N_f,), dtype=dt)
  df.create_dataset('sc', (N_sc,), dtype=dt)
  df.create_dataset('so', (N_so,), dtype=dt)
  # the actual data sets
  dc = create_enum_dataset(df, 'dc', (df['p'], df['y'], df['r'], df['sc'],
                                      df['f']))
  do = create_enum_dataset(df, 'do', (df['p'], df['y'], df['r'], df['so']))
  dt = create_enum_dataset(df, 'dt', (df['p'], df['y'], df['r']))


def read_reas(fn):
  """Read the data set from *fn*"""
  global df, dc, dc_buf, do, do_buf, dt
  # read the file into a list
  lines = list(open(fn, 'r'))
  # delete file header. TODO: check that the header is correct
  del lines[0:6]

  # clear buffers
  dc_buf[:] = numpy.nan
  do_buf[:] = numpy.nan

  # get the indices for the pollutant, year and region, to avoid repeated
  # lookups
  p_, y_, r_ = fn_parts(fn)
  p_ = numpy.where(df['p'].value == p_)[0][0]
  y_ = numpy.where(df['y'].value == y_)[0][0]
  r_ = numpy.where(df['r'].value == r_)[0][0]

  # part 1: combustion sources table
  # column headers → sectors
  cols = lines.pop(0).split()[2:]
  # add columns to list of sectors
  [ds_lookup('sc', sc, True) for sc in cols]
  # store data
  while True:
    row = lines.pop(0).split()
    if len(row) == 0:
      # empty row: table has ended
      break
    else:
      # one row per fuel
      f_ = ds_lookup('f', row[0], True)
      # one entry per combustion source
      for c, sc in enumerate(cols):
        dc_buf[ds_lookup('sc', sc),f_] = float(row[c+1])

  # part 2: non-combustion sources vector
  while len(lines):
    try:
      so, qty = lines.pop(0).split()
      qty = float(qty)
    except ValueError:
      # above code will raise an exception on non-data lines like:
      # [empty]
      # Industry [t/year]
      # Sector
      continue
    if so == 'SUB_TOTAL':
      # several SUB_TOTAL lines are given for different groups of
      # non-combustion sources, different by region and pollutant. Don't
      # save these
      continue
    elif so == 'TOTAL':
      # grand total for all pollution listed in the single file
      dt[p_,y_,r_] = qty
    else:
      # one row per non-combustion source
      do_buf[ds_lookup('so', so, True)] = qty

  # copy the results from buffers to the HDF5 file
  dc[p_,y_,r_,:,:] = dc_buf
  do[p_,y_,r_,:] = do_buf


if __name__ == '__main__':
  # names of files
  files = [s for s in os.listdir() if s[-4:] == '.txt']

  # parse the filenames for the sets of pollutants, years, and regions.
  for fn in files:
    p_, y_, r_ = fn_parts(fn)
    p.add(p_)
    y.add(y_)
    r.add(r_)

  # convert sets to lists
  p = sorted(p)
  y = sorted(y)
  r = sorted(r)

  # set up the HDF5 file
  HDF5_setup()

  # create some buffers for temporary storage. This seems to be faster
  # writing each element directly
  dc_buf = numpy.nan * numpy.ones_like(dc[0,0,0,:,:])
  do_buf = numpy.nan * numpy.ones_like(do[0,0,0,:])

  # read the files
  for i, fn in enumerate(files):
    read_reas(fn, p_, y_, r_)
    # diagnostic output every 10 lines
    if i % 10 == 0:
      print('{} / {} = {}%'.format(i, len(files), round(100. * i /
                                                        len(files), 2)))

  df.close()
