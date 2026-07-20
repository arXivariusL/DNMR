import numpy as np
import h5py as hdf
import traceback
import re

# Defines a function to convert an hdf5 group (i.e., a directory-like structure in an HDF5 file) 
# into a nested dictionary. The function recursively visits each item in the group and 
# adds it to the dictionary, converting datasets to numpy arrays when possible. 
def hdf_to_dict(g): # takes group, gives dict
    def t(n, g, d):
        ds = d
        for i in n.split('/')[:-1]:
            ds = ds[i]
        if(isinstance(g, hdf.Group)):
            ds[n.split('/')[-1]] = data_struct(hdf_to_dict(g))
        else:
            try:
                tmp = np.array(g)
            except:
                tmp = g
            ds[n.split('/')[-1]] = tmp
    d = {}
    g.visititems(lambda a,b: t(a,b,d))
    
    return d
    
class data_struct():
    data = None
    
    def __init__(self, init=None):
        self.data = { 'size': 0 }
        
        if not(init is None):
            for k, v in init.items():
                self[k] = v
        
    def __getattr__(self, attr):
        try:
            return self.data[attr]
        except:
            return getattr(self.data, attr)
        
    def __getitem__(self, attr):
        return self.data[attr]
        
    def __setitem__(self, attr, val):
        if(isinstance(val, dict)):
            self.data[attr] = data_struct(val)
        else:
            self.data[attr] = val
        
    def __add__(self, r):
        for key in list(r.keys()):
            if not(key in self.data.keys()):
                self.data[key] = r[key]
                continue
            if(key == 'size'):
                self.data['size'] += r[key]
                continue
            val = self.data[key]
            if(isinstance(self.data[key], data_struct)):
                self.data[key] = self.data[key] + r[key]
            else:
                try:
                    val = np.array(val)
                    setval = np.array(r[key])
                    if(val.ndim == 0):
                        val = np.array([val])
                    if(setval.ndim == 0):
                        setval = np.array([setval])
                    while(val.ndim < setval.ndim):
                        val = val[None,:]
                    self.data[key] = np.append(val, setval, axis=0) # if numpy
                except:
                    self.data[key] += r[key] # they're lists if not.
        return self
        
    def __repr__(self):
        s = '(DATA_STRUCT) {\n'
        for key, val in self.data.items():
            if(isinstance(val, data_struct)):
                s += f'\t{key}: '
                s += '\n\t'.join(val.__repr__().split('\n')) + '\n'
            else:
                s += f'\t{key}: {val.__repr__()}\n'
        s += '}\n'
        return s