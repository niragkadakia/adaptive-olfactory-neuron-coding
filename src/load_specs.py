"""
Functions for reading specifications file for CS decoding. 

Created by Nirag Kadakia at 9:30 08-17-2017
This work is licensed under the 
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 
International License. 
To view a copy of this license, 
visit http://creativecommons.org/licenses/by-nc-sa/4.0/.
"""

import scipy as sp
import os
from collections import OrderedDict
from local_methods import def_data_dir

data_dir = def_data_dir()

def read_specs_file(data_flag, data_dir = data_dir):
	""" 
	Function to read a specifications file.
	
	Module to gather information from specifications file about how a 
	particular 	run is to be performed for the CS decoding scheme. 
	Specs file should have format .txt and the format is as listed here:

	iter_var     sigmaSs     lin     1     10      100
	fixed_var    slkd        2
	param        nX          3
	rel_var      sigmaSs     5

	It accepts these 4 types of inputs, labeled by the first column: iterated 
	variables, fixed variables, parameters to override, and relative variables.
	For iter_var, the possible types of scaling (3rd column) are lin or exp, 
	whether the range is the direct range or 10** the range. For relative 
	variables, the 3rd column simply gives a string stating the functional 
	dependency upon an independent variable. iter_vars are also put in an 
	ordered dictionary, the keys appearing in the order listed in the specs
	file.
	
	Args: 
		data_flag: Name of specifications file.
		data_dir: Data folder, if different than in local_methods.
	
	Returns:
		list_dict: Dictionary of 4 items keyed by 'rel_vars', 
					'fixed_vars', 'params', and 'iter_vars'.	

	TODO: 
		Add variables (e.g. seeds) to be averaged over (statistics)
	"""

	filename = '%s/specs/%s.txt' % (data_dir, data_flag)	
	try:
		os.stat(filename)
	except:
		print ("There is no input file %s/specs/%s.txt" 
				% (data_dir, data_flag))
		exit()
	specs_file = open(filename, 'r')

	fixed_vars = dict()
	iter_vars = OrderedDict()
	rel_vars = dict()
	params = dict()
	
	for line in specs_file:
		if line.strip():
			if not line.startswith("#"):
				
				keys = line.split()
				var_type = keys[0]
				var_name = keys[1]
					
				if var_type == 'iter_var':
					scaling = str(keys[2])
					lo = float(keys[3])
					hi = float(keys[4])
					Nn = int(keys[5])
					if scaling == 'lin':
						iter_vars[var_name] = sp.linspace(lo, hi, Nn)
					elif scaling == 'exp':
						base = float(keys[6])
						iter_vars[var_name] = base**sp.linspace(lo, hi, Nn)
				elif var_type == 'fixed_var':
					fixed_vars[var_name] = float(keys[2])
				elif var_type == 'rel_var':
					rel_vars[var_name] = str(keys[2])
				elif var_type == 'param':
					params[var_name] = int(keys[2])
				else:
					print ('nothing')
					
	specs_file.close()
	print ('\n -- Input vars and params loaded from %s.txt\n' % data_flag)
	
	list_dict =  dict()
	for i in ('rel_vars', 'fixed_vars', 'params', 'iter_vars'):
		list_dict[i] = locals()[i]
	
	return list_dict
	
def parse_iterated_vars(iter_vars, iter_vars_idxs, vars_to_pass):	
	"""
	Parse the iterated variables from a dictionary to pass to 
	four_state_receptor_CS.
	
	Args:
		iter_vars: Dictionary of iterated variables and values.
		iter_vars_idxs: Arguments of iterated variable indices from command 
						line arguments.
		vars_to_pass: Dictionary holding as yet collected variables to pass.
		
	Returns:
		vars_to_pass: Same dictionary, now updated with the iterated variables
	"""
	
	assert len(iter_vars_idxs) == len(iter_vars), \
			"Need %s command line args for the iterated variables (%s "\
			"supplied)" % (len(iter_vars), len(iter_vars_idxs))
	
	print (' -- Running iterated variables with values:\n')
	
	for i_sys_arg, iter_var in enumerate(iter_vars.keys()):
		idx = int(iter_vars_idxs[i_sys_arg])
		vars_to_pass[iter_var] = iter_vars[iter_var][idx]
		print ('%s    \t = %s' %  (iter_var, vars_to_pass[iter_var]))
	
	return vars_to_pass
	
def parse_relative_vars(rel_vars, iter_vars, vars_to_pass):
	"""
	Parse the relatively-defined vriables from a dictionary to pass to 
	four_state_receptor_CS.
	
	Args:
		rel_vars: Dictionary of relative variables and values. Keys of
					dictionary items represent the name of dependent 
					variables; corresponding values are a string expressing
					their dependence on iterated variables, using numpy syntax.
		iter_vars: Dictionary of iterated variables.
		vars_to_pass: Dictionary holding as yet collected variables to pass.
		
	Returns:
		vars_to_pass: Same dictionary, now updated with the relative variables
	"""	
	
	print ('\n -- Variables relative to others:\n')
	
	for rel_var, var_rule in rel_vars.items():
		assert rel_var not in vars_to_pass, 'Relative variable %s is already '\
												'being iterated' % rel_var
		flag = False
		for iter_var in iter_vars.keys():
			if iter_var in var_rule:
				flag = True
				tmp_str = var_rule.replace(iter_var, '%s' % vars_to_pass[iter_var])
				vars_to_pass[rel_var] = eval(tmp_str)
				break
			else:
				continue
				
	assert flag == True, 'Assignment %s <-- %s does not depend on any '\
							'iterated variables' % (rel_var, var_rule)	

	print ('%s = %s <-- %s' % (var_rule, vars_to_pass[rel_var], rel_var))

	return vars_to_pass