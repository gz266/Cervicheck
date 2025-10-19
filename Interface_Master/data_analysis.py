import numpy as np
import scipy
from scipy.optimize import curve_fit
from sympy import symbols, diff, lambdify

def func(x, a, C):
    return a* C * ((x ** 2) - (1 / x))* np.exp(a * ((x ** 2) + (2 / x) - 3))

def func2(x, m):
    return m*(x-1)

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

    popt, pcov = curve_fit(func, x, y, maxfev=100000)
    #fit_values = fit(stretch' ,cur_stress',fit_type, 'StartPoint', [1, 1]);
    #coeff = coeffvalues(fit_values)

    eff_modulus = popt[0]*popt[1]*(-0.052*(popt[0]**3)+0.252*(popt[0]**2)+(0.053*popt[0])+1.09)

    t = symbols('t')
    f = func(x, *popt)
    d2f = diff(f, t, 2)
    d2f_func = lambdify(t, d2f, 'numpy')

    youngs_stretch = []
    youngs_stress = []

    for i in range(len(x)):
        if d2f_func(x[i]) in range (-1, 1):
            youngs_stretch.append(x[i])
            youngs_stress.append(y[i])
        else:
            break
    popt2, pcov2 = curve_fit(func2, x, y, maxfev=100000)
    #fit_values = fit(stretch' ,cur_stress',fit_type, 'StartPoint', [1, 1]);
    #coeff = coeffvalues(fit_values)

    eff_modulus = popt[0]*popt[1]*(-0.052*(popt[0]**3)+0.252*(popt[0]**2)+(0.053*popt[0])+1.09)
    youngs_modulus = popt2[0]
    intercept = -popt2[0]
    #regressResult = scipy.stats.linregress(youngs_stretch, youngs_stress)
    #youngs_modulus = regressResult.slope
    #intercept = regressResult.intercept
    print(youngs_stretch)

    return popt, eff_modulus, youngs_modulus, intercept
