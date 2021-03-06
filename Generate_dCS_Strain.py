#!/usr/bin/python

import sys
import argparse
import scipy
import h5py
import numpy as np
import os

def ReadExtrapolatedMode(p, piece, mode, order=2, ell=None):
  """ Given a file of extrapolated modes, read in the (mode)
      at a given order """
  ell = str(ell).replace('.', 'p')
  piece_dict = {"DeltaStrain" : "DeltaStrain.h5", \
          "BackgroundStrain" : "BackgroundStrain.h5", \
          "dCSModified" : "Strain_dCS_ell_" + ell + ".h5"}
  file = p + piece_dict[piece]
  l = mode[0]
  m = mode[1]
  f = h5py.File(file, 'r')
  data = f['Extrapolated_N'+str(order)+'.dir']['Y_l' + str(l) + '_m'  + str(m) + '.dat']
  time, re, im = data[:,0], data[:,1], data[:,2]
  result = re + 1j*im
  return time, result

def ComputedCSModifiedStrain(p, mode, l):
  """ Given a value of the dCS coupling constant l, a path 
      p to the extrapolated hPsi4 compute the modified gravitational wave strain """

  ## Read in the background
  time, strain = ReadExtrapolatedMode(p, "BackgroundStrain", mode)
  delta_time, delta_strain = ReadExtrapolatedMode(p, "DeltaStrain", mode)

  ## Now add the strain and delta strain together
  ## with the correct value of l
  total = strain + l**4 * delta_strain

  return time, total


def OutputdCSModifiedStrain(p, ell, only22, dropm0):
    """ Generate an h5 file with the modified strain for a 
        given value of ell """

    ## For naming the file, replace . with p because otherwise
    ## the .h5 file can't be read by catalog scripts
    name = str(ell).replace('.', 'p')
    
    OutFile = p + 'Strain_dCS_ell_' + name + '.h5'
    fOut = h5py.File(OutFile, 'w')
    
    grp = fOut.create_group("Extrapolated_N2.dir")
    
    ## Compute for only (2,2) and (2, -2) modes
    if only22:
      print("Computing for (2,2), (2,-2) modes only")

      modes = [(2,2),(2,-2)]
      for mode in modes:
        l = mode[0]
        m = mode[1]
        print("Computing for ", mode)
        time, total = ComputedCSModifiedStrain(p, mode, ell)
        ## Compute for the given mode
        dataset = grp.create_dataset("Y_l"+str(l)+"_m"+str(m)+".dat", \
        (len(time),3), dtype='f')

        dataset[:,0] = time
        dataset[:,1] = np.real(total)
        dataset[:,2] = np.imag(total)

      ## For all other modes
      l_arr = range(2, 9)
      for l in l_arr:
        print("Computing for l = ", l)

        for m in range(-l, l+1):
          mode = (l, m)
          if mode not in modes:
            print("Setting zero for ", mode)
            dataset = grp.create_dataset("Y_l"+str(l)+"_m"+str(m)+".dat", \
            (len(time),3), dtype='f')

            dataset[:,0] = np.zeros_like(time)
            dataset[:,1] = np.zeros_like(time)
            dataset[:,2] = np.zeros_like(time)
            
    ## All modes except m = 0
    elif dropm0:
        print("Computing for all modes except m = 0")
    
        l_arr = range(2, 9)

        for l in l_arr:
            print("Computing for l = ", l)

            for m in range(-l, l+1):
            
                mode = (l, m)
        
                if m != 0:
                    ## Compute the mode if not m = 0
                    time, total = ComputedCSModifiedStrain(p, mode, ell)

                    dataset = grp.create_dataset("Y_l"+str(l)+"_m"+str(m)+".dat", \
                    (len(time),3), dtype='f')

                    dataset[:,0] = time
                    dataset[:,1] = np.real(total)
                    dataset[:,2] = np.imag(total)
            
                else:
                    ## Set to zero if m = 0 
                    print("Setting zero for ", mode)
                    dataset = grp.create_dataset("Y_l"+str(l)+"_m"+str(m)+".dat", \
                    (len(time),3), dtype='f')

                    dataset[:,0] = np.zeros_like(time)
                    dataset[:,1] = np.zeros_like(time)
                    dataset[:,2] = np.zeros_like(time)
        
    ## Compute for all of the modes
    else:
        print("Computing for all of the modes")
        l_arr = range(2, 9)

        for l in l_arr:
            print("Computing for l = ", l)

            for m in range(-l, l+1):
                mode = (l, m)
                print(mode)

                ## Compute for the given mode
                time, total = ComputedCSModifiedStrain(p, mode, ell)

                dataset = grp.create_dataset("Y_l"+str(l)+"_m"+str(m)+".dat", \
                (len(time),3), dtype='f')

                dataset[:,0] = time
                dataset[:,1] = np.real(total)
                dataset[:,2] = np.imag(total)

    fOut.close()
    print("Wrote waveforms to file", OutFile)

def GetModesFromString(modes):
    """ Method to get output modes from a given string, used to specify
        the modes to the LVC file generation """
    if modes == 'all':
        modes = [[l,m] for l in range(2,9) for m in range(-l,l+1)]
    elif modes == '22only':
        modes = [[2, 2], [2, -2]]
    return modes

def GenerateStrainFiles(ell, only22, dropm0):
    """ Generates the sxs format waveform waveform for a given
        beyond-GR simulation with coupling parameter ell. 
        
        The file BeyondGRAnalysis/Waveforms/BackgroundStrain.h5 contains the strain
        of the GR background, h_GR. 
        
        Meanwhile the file BeyondGRAnalysis/Waveforms/DeltaStrain.h5 contains the 
        leading-order modification to the beyond-GR strain, delta_h. 
        
        We first generate the sxs format total beyond-GR waveform for these
        using 
        
        h = h_GR + ell^4 * delta_h. 
        
        only22 is a boolean specifying if we should only output the 22 mode, 
        which can be useful for testing purposes
        
        """
    ## Since ell has a decimal point and *.h5 readers cannot
    ## handle this decimal point, we will replace the decimal point 
    ## with the character p, ie
    ## 0.1 will become 0p1
    ell_string = str(ell).replace('.', 'p')

    ## Call to generate total waveform in sxs format
    OutputdCSModifiedStrain("Waveforms/", ell, only22, dropm0)
    
def main():
  p = argparse.ArgumentParser(description="Generate dCS waveform for a given coupling parameter value")
  p.add_argument("--ell", required=True, type=float,\
    help="Value of dCS coupling constant")
  p.add_argument('--only22', help='Only output the 22 mode', \
    dest='only22', action='store_true')
  p.add_argument('--dropm0', help='Include all modes up to l = 8 except m = 0 modes', \
    dest='dropm0', action='store_true')
  p.set_defaults(only22=False)
  p.set_defaults(dropm0=False)
  args = p.parse_args()

  GenerateStrainFiles(args.ell, args.only22, args.dropm0)

if __name__ == "__main__":
  main()
