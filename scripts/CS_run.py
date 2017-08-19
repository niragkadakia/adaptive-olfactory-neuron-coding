"""
Run a CS decoding run for one given index of a set of iterated
variables. 

Created by Nirag Kadakia at 14:40 08-17-2017
This work is licensed under the 
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 
International License. 
To view a copy of this license,
visit http://creativecommons.org/licenses/by-nc-sa/4.0/.
"""

import scipy as sp
import sys
import os
sys.path.append('../src')
from utils import merge_two_dicts, get_flag
from load_data import check_existing_file
from save_data import save_object_array
from load_specs import read_specs_file, parse_iterated_vars, \
						parse_relative_vars
from four_state_receptor_CS import four_state_receptor_CS


def CS_run():
	"""
	Run a CS decoding run for one given index of a set of iterated
	variables. 

	Data is read from a specifications file in the data_dir/specs/ 
	folder, with proper formatting given in read_specs_file.py. The
	specs file indicates the full range of the iterated variable. This
	script only produces output from one of those indices, so multiple
	runs can be performed in parallel.
	"""
	
	data_flag = get_flag()
	check_existing_file(data_flag)
	iter_var_idxs = map(int, sys.argv[2:])
	
	# Get the four dictionaries of parameters and variables, pass to locals()
	list_dict = read_specs_file(data_flag)
	for key in list_dict:
		exec("%s = list_dict[key]" % key)
	
	vars_to_pass = dict()
	vars_to_pass = parse_iterated_vars(iter_vars, iter_var_idxs, vars_to_pass)
	vars_to_pass = parse_relative_vars(rel_vars, iter_vars, vars_to_pass)
	vars_to_pass = merge_two_dicts(vars_to_pass, fixed_vars)
	vars_to_pass = merge_two_dicts(vars_to_pass, params)

	a = four_state_receptor_CS(**vars_to_pass)
	a.encode()
	a.decode()
	save_object_array(iter_vars, iter_var_idxs, a, data_flag)

if __name__ == '__main__':
	CS_run()