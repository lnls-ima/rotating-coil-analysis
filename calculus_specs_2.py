'''
Created on 30 de jun de 2016

@author: lucas.balthazar

This script is made to calculate the multipoles errors of the Booster and Storage Ring Magnets
for data analysis in rotating coil bench.
----------
P.S.: The FAC notation for pole orders: n=0(Dipole), n=1(Quadrupole), n=2(Sextupole)
      The IMA notation for pole orders: n=1(Dipole), n=2(Quadrupole), n=3(Sextupole)
----------
Parameters located: 'https://wiki-sirius.lnls.br/mediawiki/index.php/Machine:Magnets#Booster_Quadrupoles', accessed: 11/07/2016 (MM/DD/YYYY)
'''

#Library
import numpy as np
import matplotlib.pyplot as plt
import random

class constants(object):
    def __init__(self):
        self.normal_sys_monomials = np.array([])
        self.normal_sys_relative_multipoles_at_r0 = np.array([])
        self.normal_rms_monomials = np.array([])
        self.normal_rms_relative_multipoles_at_r0 = np.array([])
        self.skew_sys_monomials = np.array([])
        self.skew_sys_relative_multipoles_at_r0 = np.array([])
        self.skew_rms_monomials = np.array([])
        self.skew_rms_relative_multipoles_at_r0 = np.array([])

    def sextupole(self, r0, x):
        self.p = 2  #(SEXTUPOLE - FAC)
        self.r0 = r0/1000
        self.x = x
        # sys spec - NORMAL
        self.normal_sys_monomials = np.array([8,14])                            # This means allowed multipole error. In this case B8 and B14 (see Wiki) 
        self.normal_sys_relative_multipoles_at_r0 = np.array([-2.5e-2, -1.5e-2])
        
        # rms spec - NORMAL
        self.normal_rms_monomials = np.array([3,4,5,6,7,8,9,14])                # This are Integrated Multipoles B(3,4,5...14) calculated at r0 (B2)
        self.normal_rms_relative_multipoles_at_r0 = np.array([4,4,4,4,4,4,4,4])*1e-4
        
        # sys spec -SKEW
        self.skew_sys_monomials = np.array([2])                                                                 
        self.skew_sys_relative_multipoles_at_r0 = np.array([0])

        # rms spec - SKEW
        self.skew_rms_monomials = np.array([3,4,5,6,7,8,9,14])
        self.skew_rms_relative_multipoles_at_r0 = np.array([1,1,1,1,1,1,1,1])*1e-4

    def quadrupole_qf(self, r0, x):
        self.p = 1  #(QUADRUPOLE - FAC)
        self.r0 = r0/1000
        self.x = x
        # sys spec - NORMAL
        self.normal_sys_monomials = np.array([5,9,13])
        self.normal_sys_relative_multipoles_at_r0 = np.array([-1.0e-3, +1.1e-3, +8.0e-5])

        # rms spec - NORMAL
        self.normal_rms_monomials = np.array([2,3,4,5,6,7,8,9,13])                
        self.normal_rms_relative_multipoles_at_r0 = np.array([7,4,4,4,4,4,4,4,4])*1e-4

        # sys spec -SKEW
        self.skew_sys_monomials = np.array([1])                                                                   
        self.skew_sys_relative_multipoles_at_r0 = np.array([0])

        # rms spec - SKEW
        self.skew_rms_monomials = np.array([2,3,4,5,6,7,8,9,13])
        self.skew_rms_relative_multipoles_at_r0 = np.array([1,5,1,1,1,1,1,1,1])*1e-4

    def quadrupole_qd(self, r0, x):
        self.p = 1  #(QUADRUPOLE - FAC)
        self.r0 = r0/1000
        self.x = x
        # sys spec - NORMAL
        self.normal_sys_monomials = np.array([5,9,13])
        self.normal_sys_relative_multipoles_at_r0 = np.array([-4.7e-3, +1.2e-3, +1.2e-6])

        # rms spec - NORMAL
        self.normal_rms_monomials = np.array([2,3,4,5,6,7,8,9,13])                
        self.normal_rms_relative_multipoles_at_r0 = np.array([7,4,4,4,4,4,4,4,4])*1e-4

        # sys spec -SKEW
        self.skew_sys_monomials = np.array([1])                                                                   
        self.skew_sys_relative_multipoles_at_r0 = np.array([0])

        # rms spec - SKEW
        self.skew_rms_monomials = np.array([2,3,4,5,6,7,8,9,13])
        self.skew_rms_relative_multipoles_at_r0 = np.array([1,5,1,1,1,1,1,1,1])*1e-4   
              
    def normal_residual(self):
        #Normal residual field
        self.plot_residual_field('NORMAL', self.p, self.r0, self.x, self.normal_sys_monomials, 
                                 self.normal_sys_relative_multipoles_at_r0,
                                 self.normal_rms_monomials, self.normal_rms_relative_multipoles_at_r0)
    def skew_residual(self):
        #Skew residual field
        self.plot_residual_field('SKEW', self.p, self.r0, self.x, self.skew_sys_monomials, 
                                 self.skew_sys_relative_multipoles_at_r0, 
                                 self.skew_rms_monomials, self.skew_rms_relative_multipoles_at_r0)


    def plot_residual_field(self, label, p, r0, x, sys_monomials, sys_relative_multipoles_at_r0, 
                            rms_monomials, rms_relative_multipoles_at_r0):

        self.nr_samples = 5000
        self.gauss_trunc = 1

        #Systematic residual
        self.sys_residue = 0*x
        for i in range (len(sys_monomials)):
            self.sys_residue = self.sys_residue + 1*sys_relative_multipoles_at_r0[i]*(x/r0)**(sys_monomials[i]-p)
            
        size = len(rms_relative_multipoles_at_r0)*self.nr_samples
        rnd_grid = np.array([])

        #Making the random normal distribution
        while (len(rnd_grid) < size):           
            randomgauss = random.gauss(0,1)
            if (abs(randomgauss) > self.gauss_trunc):
                randomgauss = []
            rnd_grid = np.append(rnd_grid, randomgauss)           
        rnd_grid = rnd_grid.reshape(self.nr_samples,(size/self.nr_samples))

        max_residue = self.sys_residue
        min_residue = self.sys_residue

        #Use rows of random grid for calculate the relative rms and residual field
        for j in range (self.nr_samples): 
            rnd_vector = rnd_grid[j,:]
            rnd_relative_rms = (rms_relative_multipoles_at_r0)*rnd_vector
            rms_residue = 0
            for i in range (len(rms_monomials)):     
                rms_residue = rms_residue + 1*rnd_relative_rms[i]*(x/r0)**(rms_monomials[i]-p)
                
            residue_field = self.sys_residue + rms_residue

            #Maximum residual values
            max_residue = np.maximum(residue_field, max_residue)
            #Minimum residual values
            min_residue = np.minimum(residue_field, min_residue)

   
        self.sys_residual = self.sys_residue
        self.maximo = max_residue
        self.minimo = min_residue

        
         
##        #Plot Figure
##        plt.plot(x, self.sys_residue, '-b', label=label)
##        plt.legend(loc='best')
##        plt.plot(x, max_residue, '-r')
##        plt.plot(x, min_residue, '-r')
##        plt.title('Allowed - red, systematic - blue')
##        plt.xlabel('pos [mm]')
##        plt.ylabel('relative residual integrated field')
##        plt.grid('on')
##        plt.show()


#a = constants()
