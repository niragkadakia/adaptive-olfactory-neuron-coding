"""
Run a CS decoding run for a time-varying signal. Two odor signals 
can be loaded from distinct files. The first odor is the one to which
the system adapts and should be a slower signal than the second, to
which the system does not adapt.

Created by Nirag Kadakia at 22:26 01-17-2018
This work is licensed under the 
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 
International License. 
To view a copy of this license,
visit http://creativecommons.org/licenses/by-nc-sa/4.0/.
"""

import scipy as sp
import sys
import os
import copy
sys.path.append('../src')
from four_state_receptor_CS import four_state_receptor_CS
from utils import get_flag
from save_data import dump_objects
from load_specs import read_specs_file, compile_all_run_vars
from encode_CS import single_encode_CS
from analysis import binary_errors


def temporal_CS_run(data_flag, iter_var_idxs, sigma_Ss0=0, 
					mu_dSs_offset=0, mu_dSs_multiplier=1./3., 
					sigma_dSs_offset=0, sigma_dSs_multiplier=1./9., 
					signal_window=None):
	"""
	Run a CS decoding run for a full temporal signal trace.

	Data is read from a specifications file in the data_dir/specs/ 
	folder, with proper formatting given in read_specs_file.py. The
	specs file indicates the full range of the iterated variable; this
	script only produces output from one of those indices, so multiple
	runs can be performed in parallel.
	"""
	
	assert mu_dSs_offset >= 0, "mu_dSs_offset kwarg must be >= 0"
	assert sigma_dSs_offset >= 0, "sigma_dSs_offset kwarg must be >= 0"
	
	# Aggregate all run specifications from the specs file; instantiate model
	list_dict = read_specs_file(data_flag)
	vars_to_pass = compile_all_run_vars(list_dict, iter_var_idxs)
	obj = four_state_receptor_CS(**vars_to_pass)
		
	# Set the temporal signal array from file; truncate to signal window
	obj.set_signal_trace()
	assert sp.sum(obj.signal_trace <= 0) == 0, \
		"Signal contains negative values; increase signal_trace_offset"
	if signal_window is not None:
		obj.signal_trace_Tt = obj.signal_trace_Tt[signal_window[0]: \
													signal_window[1]]
		obj.signal_trace = obj.signal_trace[signal_window[0]: signal_window[1]]
	
	# Load dual odor dSs from file (this is considered non-adapted fluctuation
	# and should have a shorter timescale than the first odor)
	print obj.Kk_split
	if obj.Kk_split > 0:
		assert sp.sum(obj.signal_trace_2 <= 0) == 0, \
				"Signal_2 contains neg values; increase signal_trace_2_offset"
		if signal_window is not None:
			obj.signal_trace_2 = obj.signal_trace_2[signal_window[0]: \
													signal_window[1]]
			
	obj_list = []
	for iT, dt in enumerate(obj.signal_trace_Tt):
		print '%s/%s' % (iT + 1, len(obj.signal_trace)), 
		
		# Set estimation dSs values from signal trace and kwargs
		obj.mu_Ss0 = obj.signal_trace[iT]
		obj.sigma_Ss0 = sigma_Ss0
		obj.mu_dSs = mu_dSs_offset + obj.mu_Ss0*mu_dSs_multiplier
		obj.sigma_dSs = sigma_dSs_offset + obj.mu_Ss0*sigma_dSs_multiplier
		
		# Set estimation dSs values for dual odor if needed
		if obj.Kk_split > 0:
			signal_2 = obj.signal_trace_2[iT]
			obj.mu_dSs_2 = mu_dSs_offset + signal_2*mu_dSs_multiplier
			obj.sigma_dSs_2 = sigma_dSs_offset + signal_2*sigma_dSs_multiplier
	
		# Encode / decode fully first time; then just update eps and responses
		if iT == 0:
			obj = single_encode_CS(obj, list_dict['run_specs'])
		else:
			obj.set_sparse_signals()
			obj.set_temporal_adapted_epsilon()
			obj.set_measured_activity()
			obj.set_linearized_response()
		
		# Estimate signal at point iT
		obj.decode()
		
		# Deep copy to take all aspects of the object but not update it
		obj_list.append(copy.deepcopy(obj))
		
		dump_objects(obj_list, iter_var_idxs, data_flag, output=False)
	
	return obj_list
	
	
if __name__ == '__main__':
	data_flag = get_flag()
	iter_var_idxs = map(int, sys.argv[2:])
	temporal_CS_run(data_flag, iter_var_idxs)