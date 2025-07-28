import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Define the model function
def func(x, a, C):
    return a* C * ((x ** 2) - (1 / x))* np.exp(a * ((x ** 2) + (2 / x) - 3))

def align_data(stretch, stress):
    """
    Aligns the data based on the stretch and strain values.
    
    Parameters:
    stretch (1D array): Stretch factor for the analysis.
    stress (1D array): Strain data for the trial.
    
    Returns:
    aligned_stretch (1D array): Aligned stretch values.
    aligned_strain (1D array): Aligned stress values.
    """

    aligned_stretch = stretch
    aligned_stress = stress

    for i in range(1, len(stress)):
        if stress[i] == 0.:
            aligned_stress = aligned_stress[:i]
            aligned_stretch = aligned_stretch[:i]
            return aligned_stretch, aligned_stress
    
    return aligned_stretch, aligned_stress

def analyze_data(stretch, stress):
    """
    Analyze ONE set of data based on the specified fit type and stretch.
    
    Parameters:
    stretch (1D array): Stretch factor for the analysis.
    varargin (1D array): Stress data for the trial.
    
    Returns:
    popt (array): Optimal values for the parameters of the fit.
    eff_modulus (float): Effective modulus calculated from the fit parameters.
    """

    # TODO 

    eff_modulus = 0
    x = stretch
    y = stress* -1

    popt, pcov = curve_fit(func, x, y, maxfev=10000)
    #fit_values = fit(stretch' ,cur_stress',fit_type, 'StartPoint', [1, 1]);
    #coeff = coeffvalues(fit_values)
    
    alpha_coeff = 0
    C_coeff = 0
    eff_modulus = popt[0]*popt[1]*(-0.052*(popt[0]**3)+0.252*(popt[0]**2)+(0.053*popt[0])+1.09)
    
    return popt, eff_modulus

# Strain, depends on the tissue
ex_stress = np.array([-0., -1.31, -2.01, -3.25, -4.03, -4.97, -8.07, 0])

# Constants, determined by the geometry of the flex PCB
stretch = np.array([1, 1.2415, 1.406, 1.572, 1.738, 1.9045, 2.071, 2.2375])

x, y = align_data(stretch, ex_stress)
print(x)
print(y)
coefficients, modulus = analyze_data(x, y)
plt.plot(x, y*-1, 'b-', label='data')
plt.plot(x, func(x, *coefficients), 'r-')
plt.legend(['Data', 'Fit'])
plt.xlabel('Percent Strain (%)')
plt.ylabel('Stress (kPa)')
print(coefficients)
print(modulus)
plt.show()