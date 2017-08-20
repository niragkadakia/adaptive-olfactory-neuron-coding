"""
Functions for decoding a sparse vector, given linear response matrix
and vector of measurements. Can use either weak or strong 
constraint enforcement.

Created by Nirag Kadakia at 23:30 07-31-2017
This work is licensed under the 
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 
International License. 
To view a copy of this license, 
visit http://creativecommons.org/licenses/by-nc-sa/4.0/.
"""

import scipy as sp
from scipy.optimize import minimize


def decode_CS(Rr, Yy, opt_type = "L1_strong", precision = 'None', 
				init_params = [0,1]):
	"""
	CS decoding with L1 norm
	"""		

	def L1_strong(x):
		return sp.sum(abs(x))

	def L1_weak(x,*args):
		Rr, Yy, precision = args
		tmp1 = sp.sum(abs(x))
		tmp2 = precision*sp.sum((sp.dot(Rr, x) - Yy)**2.0)
		return tmp1+tmp2

	Nn = len(Rr[0,:])
	
	if opt_type == "L1_strong":
		constraints = ({'type': 'eq', 'fun': lambda x: sp.dot(Rr, x) - Yy})
		res = minimize(L1_strong, 
						sp.random.normal(init_params[0], init_params[1], Nn), 
						method='SLSQP', constraints = constraints)
	elif opt_type == "L1_weak":
		res = minimize(L1_weak, 
						sp.random.normal(init_params[0], init_params[1], Nn), 
						args = (Rr, Yy, precision), method='SLSQP')
	
	return res.x