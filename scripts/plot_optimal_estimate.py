"""
Plot the optimal estimate for given runs, one by one.

Created by Nirag Kadakia at 17:00 08-27-2017
This work is licensed under the 
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 
International License. 
To view a copy of this license,
visit http://creativecommons.org/licenses/by-nc-sa/4.0/.
"""


import scipy as sp
import sys
sys.path.append('../src')
from utils import get_flag
from load_specs import read_specs_file
from load_data import load_aggregated_object_list
from load_data import load_errors
import matplotlib.pyplot as plt
	

def plot_optimal_estimate(data_flag, axes_to_plot=[0, 1], fixed_axes=dict()):
	"""
	Calculate estimation error of inferred signal in compressed sensing 
	decoding module CS_run.py.
	"""

	list_dict = read_specs_file(data_flag)
	for key in list_dict:
		exec("%s = list_dict[key]" % key)

	iter_vars_dims = []
	for iter_var in iter_vars:
		iter_vars_dims.append(len(iter_vars[iter_var]))		
	it = sp.nditer(sp.zeros(iter_vars_dims), flags = ['multi_index'])	

	print ('Loading object list...')
	CS_object_array = load_aggregated_object_list(iter_vars_dims, data_flag)
	print ('...loaded.')

	errors = load_errors(data_flag)
	# 2D for now.
	assert (len(errors.shape) == 2), "Need a rank-2 error array"
	
	for idx in range(len(errors[:,0])):
		opt_idx = sp.argmin(errors[idx,:])
		bad_idx = sp.argmax(errors[idx,:])
		bkgrnd = CS_object_array[idx, opt_idx].Ss0
		plt.plot(CS_object_array[idx, opt_idx].dSs_est + bkgrnd, color='orange')
		plt.plot(CS_object_array[idx, bad_idx].dSs_est + bkgrnd, color='blue')
		plt.plot(CS_object_array[idx, opt_idx].dSs + bkgrnd, color='k', linestyle = '--')
		plt.title(idx)
		plt.show()
		
if __name__ == '__main__':
	data_flag = get_flag()
	plot_optimal_estimate(data_flag, axes_to_plot=[1,2], fixed_axes=dict(mu_Ss0=0))
