"""
Calculate estimation error of inferred signal in compressed sensing 
decoding for a full signal trace in time. Success ratios are calculated
as a function of time, 


Created by Nirag Kadakia at 15:00 09-05-2017
This work is licensed under the 
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 
International License. 
To view a copy of this license,
visit http://creativecommons.org/licenses/by-nc-sa/4.0/.
"""


import scipy as sp
import sys
sys.path.append('../src')
from load_specs import read_specs_file
from load_data import load_objects
from save_data import save_temporal_errors
from analysis import binary_errors, binary_success


def calculate_temporal_success(data_flags, nonzero_bounds=[0.75, 1.25], 
							zero_bound=1./10., threshold_pct_nonzero=100, 
							threshold_pct_zero=100):
	"""
	Compile all the data from all temporal traces for all iterated variables.
	Saves zero/nonzero errors, successes, and epsilons for each point
	along the signal trace. 
	"""
	
	# Get full iterated variable indices from specss
	list_dict = read_specs_file(data_flag)
	iter_vars = list_dict['iter_vars']
	iter_vars_dims = []
	for iter_var in list_dict['iter_vars']:
		iter_vars_dims.append(len(iter_vars[iter_var]))		
	it = sp.nditer(sp.zeros(iter_vars_dims), flags = ['multi_index'])	
	
	# Use first index to get signal and Tt
	CS_init_array = load_objects(list(it.multi_index), data_flag)
	nT = len(CS_init_array)
	Tt = CS_init_array[0].signal_trace_Tt
	signal = CS_init_array[0].signal_trace
	
	# To hold data for each timepoint, for each iter_var_idx
	data = dict()
	array_shape = sp.hstack((nT, iter_vars_dims))
	data['success_ratios'] = sp.zeros(array_shape)
	data['nonzero_errors'] = sp.zeros(array_shape)
	data['zero_errors'] = sp.zeros(array_shape)
	data['epsilons'] = sp.zeros(array_shape)
	
	while not it.finished:
		
		# Load temporal data trace for this particular iterated variable index
		print 'Loading index:', it.multi_index
		temporal_CS_array = load_objects(list(it.multi_index), data_flag)
		
		# Errors and success ratios timepoint-by-timepoint
		for iT, dt in enumerate(Tt):
			full_idx = (iT, ) + it.multi_index
			
			errors = binary_errors(temporal_CS_array[iT], 
									nonzero_bounds=nonzero_bounds,
									zero_bound=zero_bound)
			success = binary_success(
						errors['errors_nonzero'], errors['errors_zero'], 
						threshold_pct_nonzero=threshold_pct_nonzero,
						threshold_pct_zero=threshold_pct_zero)
			
			data['nonzero_errors'][full_idx] = errors['errors_nonzero']
			data['zero_errors'][full_idx] = errors['errors_zero']
			data['success_ratios'][full_idx] = success
			data['epsilons'][full_idx] = sp.average(temporal_CS_array[iT].eps)
			
		save_temporal_errors(data, data_flag)
			
		it.iternext()
	
	
if __name__ == '__main__':
	data_flag = sys.argv[1]
	calculate_temporal_success(data_flag)