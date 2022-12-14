# -*- coding: utf-8 -*-

##
# Copyright (с) Ildar Bikmamatov 2022
# License: MIT
##

import torch, os, math, random, time, sys, io
import torch.nn.functional as F
import numpy as np

from PIL import Image, ImageDraw
from torch import nn
from torch.utils.data import TensorDataset

from tiny_ai_helper import *



def data_normalize_x(data_x):
	
	"""
	Нормализация датасета по x
	"""
	
	data_x = torch.from_numpy(data_x)
	data_x = data_x.to(torch.float32) / 255.0
	
	return data_x



def data_normalize_y(data_y):
	
	"""
	Нормализация датасета по y
	"""
	
	data_y = list(map(get_vector_from_answer(10), data_y))
	data_y = torch.tensor( data_y )
	
	return data_y
	


class CoreModel(AbstractModel):
	
	
	def __init__(self):
		AbstractModel.__init__(self)
		
		self.batch_size = 256
		self.input_shape = (28,28)
		self.output_shape = (10)
		self.mnist_data = None
		
	
	def convert_batch(self, x=None, y=None):
		
		"""
		Convert batch
		"""
		
		"""
		if x is not None:
			x = x.to(torch.float) / 255.0
		
		if y is not None:
			y = y.to(torch.float)
		"""
		
		return x, y
	
	
	def get_train_dataset(self, **kwargs):
		
		"""
		Returns normalized train and test datasets
		"""
		
		data_path = os.path.join(os.getcwd(), "data", "mnist.npz")
		
		if self.mnist_data is None:
			self.mnist_data = np.load(data_path, allow_pickle=True)
		
		x_train = data_normalize_x(self.mnist_data["x_train"])
		y_train = data_normalize_y(self.mnist_data["y_train"])
		x_test = data_normalize_x(self.mnist_data["x_test"])
		y_test = data_normalize_y(self.mnist_data["y_test"])
		
		train_dataset = TensorDataset( x_train, y_train )
		test_dataset = TensorDataset( x_test, y_test )
		
		return train_dataset, test_dataset
	
	
	def on_end_epoch(self, **kwargs):
		
		"""
		On epoch end
		"""
		
		epoch_number = self.train_status.epoch_number
		acc_train = self.train_status.get_acc_train()
		acc_test = self.train_status.get_acc_test()
		acc_rel = self.train_status.get_acc_rel()
		loss_test = self.train_status.get_loss_test()
		
		if epoch_number >= 3:
			self.stop_training()
			
		if epoch_number >= 50:
			self.stop_training()
		
		if acc_train > 0.95 and epoch_number >= 10:
			self.stop_training()
		
		if acc_test > 0.95  and epoch_number >= 10:
			self.stop_training()
		
		if acc_rel > 1.5 and acc_train > 0.8:
			self.stop_training()
		
		if loss_test < 0.001 and epoch_number >= 10:
			self.stop_training()
		
		self.save()


def create_model(model_name):
	
	model = CoreModel()
	
	if model_name == "4new":
		
		model.create_model_ex(
			
			#debug=True,
			model_name=model_name,
			
			layers=[
				layer("InsertFirstAxis"),
				
				layer("Conv2d", 32, kernel_size=3, padding=(1,1)),
				layer("Relu"),
				layer("MaxPool2d", kernel_size=2, stride=2),
				
				layer("Conv2d", 128, kernel_size=3, padding=(1,1)),
				layer("Relu"),
				layer("MaxPool2d", kernel_size=2, stride=2),
				
				layer("Flat"),
				
				layer("Dropout", 0.25),
				layer("Linear", 512),
				layer("Relu"),
				
				layer("Dropout", 0.50),
				layer("Linear", model.output_shape),
				layer("Softmax"),
			],
			
		)
	
	
	elif model_name == "4old":
		
		class Module(nn.Module):
			
			def __init__(self, model):
				super(Module, self).__init__()
				
				self.model = model
				
				# Дополнительные слои
				self.softmax = nn.Softmax(-1)
				self.max_pool = nn.MaxPool2d(2, 2)
				self.drop25 = nn.Dropout(0.25)
				self.drop50 = nn.Dropout(0.50)
				
				# Сверточный слой
				self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=(1,1))
				self.conv2 = nn.Conv2d(32, 128, kernel_size=3, padding=(1,1))
				
				# Полносвязный слой
				self.fc1 = nn.Linear(6272, 512)
				self.fc2 = nn.Linear(512, model.output_shape)
			
			
			def forward(self, x):
				
				# None, 28, 28 => None, 1, 28, 28
				x = x[:,None,:]
				
				# Сверточный слой 1
				# Вход: 1, 28, 28
				x = F.relu(self.conv1(x))
				
				# Выход: 32, 28, 28
				
				# Макс пулинг
				x = self.max_pool(x)
				
				# Выход: 32, 14, 14
				
				# Сверточный слой 2
				x = F.relu(self.conv2(x))
				
				# Выход: 128, 14, 14
				
				# Макс пулинг
				x = self.max_pool(x)
				
				# Выход: 128, 7, 7
				
				# Выравнивающий слой
				x = self.drop25(x)
				x = x.view(-1, 6272)
				
				# Выход: 6272
				
				# Полносвязный слои
				x = F.relu(self.fc1(x))
				x = self.drop50(x)
				x = self.fc2(x)
				x = self.softmax(x)
				
				return x
		
		model.module = Module(model)
		
	
	if model.optimizer is None:
		model.optimizer = torch.optim.Adam(model.module.parameters(), lr=3e-4)
		
	if model.loss is None:
		model.loss = nn.MSELoss()
	
	return model