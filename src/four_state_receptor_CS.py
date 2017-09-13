"""
Object to encode and decode sparse signals using compressed sensing
but with passing a sparse odor signal through a sensory system 
described by a 4-state receptor system. Off and on states 
are distinguished here, and binding kinetics are assumed fast 
enough to leave near the steady state limit. 

The response matrix is assumed to be a linearization of the full
nonlinear response. This linearization is essentially the matrix of 
inverse disassociation constants. This script tests the decoding 
fidelity for various choices of the  mean value of the inverse K. 

Created by Nirag Kadakia at 23:30 07-31-2017
This work is licensed under the 
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 
International License. 
To view a copy of this license, 
visit http://creativecommons.org/licenses/by-nc-sa/4.0/.
"""

import scipy as sp
import sys
sys.path.append('../src')
from lin_alg_structs import random_matrix, sparse_vector, sparse_vector_bkgrnd
from kinetics import bkgrnd_activity, linear_gain, receptor_activity, \
						free_energy, Kk2_samples, Kk2_eval_normal_activity, \
						Kk2_eval_exponential_activity
from optimize import decode_CS, decode_nonlinear_CS
from utils import clip_array


INT_PARAMS = ['Nn', 'Kk', 'Mm', 'seed_Ss0', 'seed_dSs', 'seed_Kk1', 
				'seed_Kk2', 'seed_receptor_activity']


class four_state_receptor_CS:	
	"""	
	Object for encoding and decoding a four-state receptor model 
	using compressed sensing
	"""

	def __init__(self, **kwargs):
	
		# Set system parameters
		self.Nn = 50
		self.Kk = 5
		self.Mm = 20

		# Set random seeds
		self.seed_Ss0 = 1
		self.seed_dSs = 1
		self.seed_Kk1 = 1
		self.seed_Kk2 = 1
		self.seed_eps = 1
		self.seed_receptor_activity = 1
		self.seed_adapted_activity = 1
		
		# Fluctuations
		self.mu_dSs = 0.3
		self.sigma_dSs = 0.1
		
		# Background
		self.mu_Ss0 = 1.
		self.sigma_Ss0 = 0.001
		
		# K1
		self.mu_Kk1_lo = 1e4
		self.mu_Kk1_hi = 1e4
		self.sigma_Kk1_lo = 1e3
		self.sigma_Kk1_hi = 1e3
		
		# K2
		self.mu_Kk2_lo = 1e-3
		self.mu_Kk2_hi = 1e-3
		self.sigma_Kk2_lo = 1e-4
		self.sigma_Kk2_hi = 1e-4
		
		# K1-K2 mixture	
		self.mu_Kk2_2 = 1e-3
		self.sigma_Kk2_2 = 1e-4
		self.Kk2_p = 0.5
		
		# Free energy statistics
		self.mu_eps = 5.0
		self.sigma_eps = 0.0
		
		# Fixed tuning curve statistics for adapted individual activity. 
		self.receptor_tuning_center_mean = 0.2
		self.receptor_tuning_center_dev = 0
		self.receptor_tuning_range_lo = 0
		self.receptor_tuning_range_hi = 0.3
		
		# Fix tuning curve statistics for adapted full activity
		self.adapted_activity_mu = 0.5
		self.adapted_activity_sigma = 0.01
		
		# Estimate full signal or just mu_dSs above background?
		self.estimate_full_signal = True 
		
		# Overwrite variables with passed arguments	
		for key in kwargs:
			if key in INT_PARAMS:
				exec ('self.%s = int(kwargs[key])' % key)
			else:
				exec ('self.%s = kwargs[key]' % key)
			
	def set_signals(self):
		self.params_dSs = [self.mu_dSs, self.sigma_dSs]
		self.params_Ss0 = [self.mu_Ss0, self.sigma_Ss0]
		self.dSs, self.idxs = sparse_vector([self.Nn, self.Kk], 
											self.params_dSs, 
											seed = self.seed_dSs)
		
		# Ss0 is the ideal (learned) background stimulus without noise
		self.Ss0, self.Ss0_noisy = sparse_vector_bkgrnd([self.Nn, self.Kk], 
														self.idxs, 
														self.params_Ss0, 
														seed = self.seed_Ss0)
		
		# The true signal, including background noise
		self.Ss = self.dSs + self.Ss0_noisy
	
	def set_adapted_free_energy(self):
		# Set free energy based on adapted activity activity
		activity_stats = [self.adapted_activity_mu, self.adapted_activity_sigma]
		adapted_activity = random_matrix([self.Mm], params=activity_stats, 
									seed=self.seed_adapted_activity)
		self.eps = free_energy(self.Ss0, self.Kk1, self.Kk2, adapted_activity)
		
	def set_random_free_energy(self):
		# Free energy as random vector if assigned as such		
		self.eps = random_matrix([self.Mm], [self.mu_eps, self.sigma_eps], 
									seed = self.seed_eps)

	def set_normal_Kk_Kk2_mixture(self):
		# Define Kk matrices as being chosen from a Gaussian mixture
		params_Kk1 = [self.mu_Kk1, self.sigma_Kk1]
		self.Kk1 = random_matrix([self.Mm, self.Nn], params_Kk1, 
									seed = self.seed_Kk1)
		
		assert 0 <= self.Kk2_p <= 1., "Mixture ratio must be between 0 and 1"
		
		num_comp1 = int(self.Kk2_p*self.Mm)
		num_comp2 = self.Mm - num_comp1
		self.Kk2 = sp.zeros(self.Kk1.shape)
		params_Kk2 = [self.mu_Kk2, self.sigma_Kk2]
		
		self.Kk2[:num_comp1, :] = random_matrix([num_comp1, self.Nn], 
										params_Kk2, seed = self.seed_Kk2)		
		params_Kk2_2 = [self.mu_Kk2_2, self.sigma_Kk2_2]
		self.Kk2[num_comp1:, :] = random_matrix([num_comp2, self.Nn], 
										params_Kk2_2, seed = self.seed_Kk2)
								
									
	def set_normal_Kk(self, clip=True):	
		# Define class object numpy array of Kk1 and Kk2 matrix, given 
		# prescribed Gaussian statistics.
		Kk1_mus = random_matrix([self.Mm], params=[self.mu_Kk1_lo, 
								self.mu_Kk1_hi], type='uniform',
								seed=self.seed_Kk1)
		Kk1_sigmas = random_matrix([self.Mm], params=[self.sigma_Kk1_lo, 
									self.sigma_Kk1_hi], type='uniform',
									seed=self.seed_Kk1)
		Kk2_mus = random_matrix([self.Mm], params=[self.mu_Kk2_lo, 
								self.mu_Kk2_hi], type='uniform',
								seed=self.seed_Kk2)
		Kk2_sigmas = random_matrix([self.Mm], params=[self.sigma_Kk2_lo, 
									self.sigma_Kk2_hi], type='uniform',
									seed=self.seed_Kk2)
		
		self.Kk1 = random_matrix([self.Mm, self.Nn], [Kk1_mus, Kk1_sigmas], 
									type='rank2_row_gaussian', seed = self.seed_Kk1)
		self.Kk2 = random_matrix([self.Mm, self.Nn], [Kk2_mus, Kk2_sigmas],
									type='rank2_row_gaussian', seed = self.seed_Kk2)
		
		if clip == True:
			array_dict = clip_array(dict(Kk1 = self.Kk1, Kk2 = self.Kk2), max = 1e-2)
			self.Kk1 = array_dict['Kk1']
			self.Kk2 = array_dict['Kk2']
			
	def set_Kk2_normal_activity(self, **kwargs):
		# Define numpy array of Kk2 matrix, given prescribed monomolecular 
		# tuning curve statistics, and Kk1 matrix from a Gaussian prior.
		# kwargs allow overriding parameters for user-defined matrix as well.
		
		shape = [self.Mm, self.Nn]
		
		params_Kk1 = [self.mu_Kk1, self.sigma_Kk1]
		self.Kk1 = random_matrix(shape, params_Kk1, seed=self.seed_Kk1)
	
		center_mean = self.receptor_tuning_center_mean
		center_dev = self.receptor_tuning_center_dev
		range_lo = self.receptor_tuning_range_lo
		range_hi = self.receptor_tuning_range_hi
		mu_Ss0 = self.mu_Ss0
		mu_eps = self.mu_eps
		seed_Kk2 = self.seed_Kk2
		
		for key in kwargs:
			exec ('%s = kwargs[key]' % key)
		
		center_stats = [center_mean, center_dev]
		range_stats = [range_lo, range_hi]
		activity_mus = random_matrix([self.Mm], params=center_stats, 
										type='normal',
										seed=self.seed_receptor_activity)
		activity_sigmas = random_matrix([self.Mm], params=range_stats, 
										type='uniform',
										seed=self.seed_receptor_activity)
		self.Kk2 = Kk2_eval_normal_activity(shape, activity_mus, 
											activity_sigmas, mu_Ss0, mu_eps, 
											seed_Kk2)
		
		
	def set_Kk2_exponential_activity(self):
		# Define numpy array of Kk2 matrix, given prescribed monomolecular 
		# tuning curve statistics, and Kk1 matrix from a Gaussian prior.
		params_Kk1 = [self.mu_Kk1, self.sigma_Kk1]
		receptor_tuning_center = [self.receptor_tuning_center_mean, 
										self.receptor_tuning_center_dev]
		
		receptor_activity_mus = random_matrix([self.Mm], 
										params=receptor_tuning_center,
										type='normal', 
										seed = self.seed_receptor_activity)
		
		self.Kk2 = Kk2_eval_exponential_activity([self.Mm, self.Nn], 
										receptor_activity_mus, self.mu_Ss0,
										self.mu_eps, self.seed_Kk2)
		
		self.Kk1 = random_matrix([self.Mm, self.Nn], params_Kk1, 
									seed = self.seed_Kk1)
	
	def set_measured_activity(self):
		# True receptor activity
		self.Yy = receptor_activity(self.Ss, self.Kk1, self.Kk2, self.eps)
		
		# Learned background activity only utilizes average background signal 
		self.Yy0 = bkgrnd_activity(self.Ss0, self.Kk1, self.Kk2, self.eps)
		
		# Measured response above background
		self.dYy = self.Yy - self.Yy0

	def set_linearized_response(self):
		# Linearized response can only use the learned background, or ignore
		# that knowledge
		if estimate_full_signal == True:
			self.Rr = linear_gain(self.Ss, self.Kk1, self.Kk2, self.eps)
		else:
			self.Rr = linear_gain(self.Ss0, self.Kk1, self.Kk2, self.eps)
			
	def encode_normal_activity(self, **kwargs):
		# Run all functions to encode the response when the tuning curves
		# are assumed normal, and Kk matrices generated thereof.
		self.set_signals()
		self.set_random_free_energy()
		self.set_Kk2_normal_activity(**kwargs)
		self.set_measured_activity()
		self.set_linearized_response()
	
	def encode_exponential_activity(self):
		# Run all functions to encode the response when the tuning curves
		# are assumed normal, and Kk matrices generated thereof.
		self.set_signals()
		self.set_random_free_energy()
		self.set_Kk2_exponential_activity()
		self.set_measured_activity()
		self.set_linearized_response()
	
	def encode_normal_Kk(self):
		# Run all functions to encode the response when the Kk matrices
		# are assumed normal.
		self.set_signals()
		self.set_random_free_energy()
		self.set_normal_Kk()
		self.set_measured_activity()
		self.set_linearized_response()
	
	def encode_adapted_normal_activity(self):
		# Assume entire activity has adapted, not activity to single molecules.
		self.set_signals()
		self.set_normal_Kk()
		self.set_adapted_free_energy()
		self.set_measured_activity()
		self.set_linearized_response()

	def encode_adapted_normal_activity_Kk2_mixture(self):
		# Assume entire activity has adapted, not activity to single molecules.
		self.set_signals()
		self.set_normal_Kk_Kk2_mixture()
		self.set_adapted_free_energy()
		self.set_measured_activity()
		self.set_linearized_response()
		
	def decode(self):
		if estimate_full_signal == True:
			self.dSs_est = decode_CS(self.Rr, self.Yy)	
		else:
			self.dSs_est = decode_CS(self.Rr, self.dYy)	
		
	def decode_nonlinear(self):
		self.dSs_est = decode_nonlinear_CS(self)
		
