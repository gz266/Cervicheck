import numpy as np
import matplotlib.pyplot as plt
import statistics
from scipy.optimize import curve_fit

# Define the model function
def fittype(x, a, C):
    return a* C * ((x ^ 2) - (1 / x))* np.exp(a * ((x ^ 2) + (2 / x) - 3))

# Stretch is dependent on the geometry of the flex PCB
stretch = np.array([1, 1.2415, 1.406, 1.572, 1.738, 1.9045, 2.071, 2.2375])

def analyze_data(fit_type, stretch, varargin):
    """
    Analyze ONE set of data based on the specified fit type and stretch.
    
    Parameters:
    fit_type (str): Type of fit to apply.
    stretch (1D array): Stretch factor for the analysis.
    varargin (1D array): Stress data for the trial.
    
    Returns:
    alpha_coeff (float):
    C_coeff (float):
    eff_modulus (float):
    mean_modulus (float):
    std_modulus (float):
    """
    alpha_coeff = np.zeros(len(varargin))
    C_coeff = np.zeros(len(varargin))
    eff_modulus = np.zeros(len(varargin))
    
    stress = [varargin]* -1
    stress.prepend(0)

    fit_values = fit(stretch' ,cur_stress',fit_type, 'StartPoint', [1, 1]);
    coeff = coeffvalues(fit_values)
    alpha_coeff[t] = coeff[1]
    C_coeff[t] = coeff[2]
    eff_modulus[t] = alpha_coeff[t]*C_coeff[t]*(-0.052*(alpha_coeff[t]^3)+0.252*(alpha_coeff[t]^2)+(0.053*alpha_coeff[t])+1.09)
    
    return alpha_coeff, C_coeff, eff_modulus