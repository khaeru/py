"""Enumerated array wrapper around h5py.Dataset"""
import numpy


__all__ = [
  'EnumDataset',
  'create_enum_dataset',
  ]


def create_enum_dataset(f, name, indices, dtype=None):
  """Create a dataset in *f* with the given *name* and *indices*
  
  Returns an EnumDataset wrapping the new h5py.Dataset *name*.
  """
  ds = f.create_dataset(name, tuple([len(i) for i in indices]),
                        dtype=dtype)
  for i, ds_i in enumerate(indices):
    ds.dims.create_scale(ds_i, ds_i.name)
    ds.dims[i].attach_scale(ds_i)
  return EnumDataset(ds)


class EnumDataset:
  """Enumerated wrapper around an h5py.Dataset
  
  This class expects that at least 1 "scale" dataset has been attached
  to each dimension of the h5py.Dataset passed to the constructor. The
  values of the scale dataset may be used directly to access data.
  
  TODO: add a `check` method (maybe automatic) that ensures the
        dimension scales are properly arranged
  """
  def __init__(self, ds):
    self._ds = ds

  def __getitem__(self, key):
    try:
      return self._ds[key]
    except (TypeError, ValueError):
      return self._ds[self._indices(key)]

  def __setitem__(self, key, value):
    try:
      self._ds[key] = value
    except (TypeError, ValueError):
      self._ds[self._indices(key)] = value

  def _indices(self, key):
    """Return a converted *key* that can be used to index the h5py.Dataset"""
    key = key if isinstance(key, tuple) else (key,)

    # require explicit mention of each dimension in the key
    if len(key) != len(self._ds.dims):
      raise KeyError('Expected {} dimension(s), got {}: {}'.format(
        len(self._ds.shape), len(key), key))

    # process the key dimension-wise
    result = []
    for i, k in enumerate(key):
      if isinstance(k, slice):
        # pass slice objects through unchanged
        result.append(k)
        continue

      # get the labels for the current dimension
      dim = self._ds.dims[i].values()[0].value

      k = k if isinstance(k, tuple) else (k,)
      # k is a list (possibly length 1) of labels or indices for
      # dimension `i`. For each label, find its index in the list of
      # labels associated with the dimension
      indices = []
      for k_ in k:
        if isinstance(k_, (int, numpy.integer)):
          # integer: use as index directly
          indices.append(k_)
        else:
          # label: find its index
          indices.append(numpy.where(dim == k_)[0][0])
      result.append(indices[0] if len(indices) == 1 else tuple(indices))

    # convert the return value to a tuple
    return tuple(result)


def test():
#if __name__ == '__main__':
  """Testing code"""
  import h5py
  f = h5py.File('foo.h5', 'w')
  dt_str = h5py.special_dtype(vlen=str)

  rs = f.create_dataset('rs', (5,), dt_str)
  rs[:] = ['BEJ', 'ANH', 'CHQ', 'FUJ', 'GAN']

  g = f.create_dataset('g', (3,), dt_str)
  g[:] = ['c', 'TRP', 'OIL']

  ea = create_enum_dataset(f, 'data', (rs, g))
  ea[:] = numpy.arange(15).reshape((5,3))

  print(f['data'][0,(0,1,2)])
  print(ea['BEJ',:])
  print(ea[:,'TRP'])
  print(ea['BEJ','TRP'])
