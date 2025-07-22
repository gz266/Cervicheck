"""
Call on Data Analysis script
"""

import matlab.engine
eng = matlab.engine.start_matlab()
eng.cd(r'MatlabPythonControl', nargout=0)
eng.analyze(eng.cauchy, eng.stretch, eng.s1)