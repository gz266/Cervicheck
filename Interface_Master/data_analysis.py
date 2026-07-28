import numpy as np
import scipy
from scipy.optimize import curve_fit
from sympy import symbols, diff, lambdify

def func(x, a, C):
    return a* C * ((x ** 2) - (1 / x))* np.exp(a * ((x ** 2) + (2 / x) - 3))

def func2(x, m):
    return m*(x-1)

def align_data(strain, stress):
    """
    Aligns the data based on the stretch and strain values.
    
    Parameters:
    strain (1D array): Strain data for the analysis.
    stress (1D array): Stress data for the trial.
    
    Returns:
    aligned_strain (1D array): Aligned strain values.
    aligned_stress (1D array): Aligned stress values.
    """

    strain = np.asarray(strain, dtype=float)
    stress = np.asarray(stress, dtype=float)

    # Avoid deleting entries while iterating (which shifts indices and can skip items).
    # Use boolean masking to keep entries where stress magnitude is >= 0.01
    mask = np.abs(stress) >= 0.01

    # Built-in anchor point: with no pressure applied the tissue is unstretched,
    # so (strain=1, stress=0) always holds. Prepended explicitly rather than relying
    # on index 0 of the incoming arrays, and the mask above has already dropped the
    # zero-stress entries so this cannot be double-counted.
    aligned_strain = np.concatenate(([1.0], strain[mask]))
    aligned_stress = np.concatenate(([0.0], stress[mask]))

    return aligned_strain, aligned_stress

def analyze_data(strain, stress):
    """
    Analyze ONE set of data based on the specified fit type and strain.
    
    Parameters:
    strain (1D array): Strain data for the analysis.
    stress (1D array): Stress data for the trial.
    
    Returns:
    popt (array): Optimal values for the parameters of the fit.
    eff_modulus (float): Effective modulus calculated from the fit parameters.
    """

    # TODO 

    eff_modulus = 0
    x = strain
    y = stress* -1

    popt, pcov = curve_fit(func, x, y, maxfev=100000)
    #fit_values = fit(strain' ,cur_stress',fit_type, 'StartPoint', [1, 1]);
    #coeff = coeffvalues(fit_values)

    eff_modulus = popt[0]*popt[1]*(-0.052*(popt[0]**3)+0.252*(popt[0]**2)+(0.053*popt[0])+1.09)

    t = symbols('t')
    f = func(x, *popt)
    d2f = diff(f, t, 2)
    d2f_func = lambdify(t, d2f, 'numpy')

    youngs_strain = []
    youngs_stress = []

    for i in range(len(x)):
        if d2f_func(x[i]) in range (-1, 1):
            youngs_strain.append(x[i])
            youngs_stress.append(y[i])
        else:
            break
    popt2, pcov2 = curve_fit(func2, x, y, maxfev=100000)
    #fit_values = fit(strain' ,cur_stress',fit_type, 'StartPoint', [1, 1]);
    #coeff = coeffvalues(fit_values)

    eff_modulus = popt[0]*popt[1]*(-0.052*(popt[0]**3)+0.252*(popt[0]**2)+(0.053*popt[0])+1.09)
    youngs_modulus = popt2[0]
    intercept = -popt2[0]
    #regressResult = scipy.stats.linregress(youngs_strain, youngs_stress)
    #youngs_modulus = regressResult.slope
    #intercept = regressResult.intercept
    print(youngs_strain)

    return popt, eff_modulus, youngs_modulus, intercept
