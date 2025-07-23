import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Define the model function
def func(x, a, C):
    return a* C * ((x ** 2) - (1 / x))* np.exp(a * ((x ** 2) + (2 / x) - 3))

# Strain, depends on the tissue
ex_stress = np.array([0, -1, -2.35, -2.99, -3.96, -5.01, -9.31, -10.02])

# Constants, determined by the geometry of the flex PCB
stretch = np.array([1, 1.2415, 1.406, 1.572, 1.738, 1.9045, 2.071, 2.2375])

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

    popt, pcov = curve_fit(func, x, y)
    #fit_values = fit(stretch' ,cur_stress',fit_type, 'StartPoint', [1, 1]);
    #coeff = coeffvalues(fit_values)
    
    alpha_coeff = 0
    C_coeff = 0
    eff_modulus = alpha_coeff*C_coeff*(-0.052*(alpha_coeff^3)+0.252*(alpha_coeff^2)+(0.053*alpha_coeff)+1.09)
    
    return popt, eff_modulus

coefficients, modulus = analyze_data(stretch, ex_stress)
plt.plot(stretch, ex_stress*-1, 'b-', label='data')
plt.plot(stretch, func(stretch, *coefficients), 'r-')
plt.legend(['Data', 'Fit'])
plt.xlabel('Percent Strain (%)')
plt.ylabel('Stress (kPa)')
print(coefficients)
print(modulus)
plt.show()

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