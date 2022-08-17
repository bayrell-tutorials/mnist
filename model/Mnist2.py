# -*- coding: utf-8 -*-

##
# Copyright (с) Ildar Bikmamatov 2022
# License: MIT
##

import os
from .Mnist import Mnist


class Mnist2(Mnist):
	
	def get_name(self):
		r"""
		Название сети
		"""
		return os.path.join("data", "model", "2")
	
	
	def create_model(self):
		
		Mnist.create_model(self)
		
		self.max_acc = 0.95
		self.max_epochs = 50
		self.min_epochs = 10
		self.batch_size = 128
		self.input_shape = (28,28)
		self.output_shape = (10)
		
		import torch
		from torch import nn
		import torch.nn.functional as F
		
		class Model(nn.Module):
			def __init__(self, net):
				super(Model, self).__init__()
				
				self.net = net
				
				# Дополнительные слои
				self.max_pool = nn.MaxPool2d(2, 2)
				self.drop25 = nn.Dropout(0.25)
				self.drop50 = nn.Dropout(0.50)
				
				# Сверточный слой
				self.conv1 = nn.Conv2d(1, 128, kernel_size=3, padding=(1,1))
				self.conv2 = nn.Conv2d(128, 64, kernel_size=3, padding=(1,1))
				
				# Полносвязный слой
				self.fc1 = nn.Linear(3136, 256)
				self.fc2 = nn.Linear(256, net.output_shape)
			
			
			def forward(self, x):
				
				if len(x.shape) == 2:
					x = x[None,:]
				else:
					x = x[:,None,:]
				
				self.net.print_debug("Input:", x.shape)
				
				# Сверточный слой 1
				# Вход: 1, 28, 28
				x = F.relu(self.conv1(x))
				self.net.print_debug("Conv1:", x.shape)
				
				# Выход: 128, 28, 28
				
				# Макс пулинг
				x = self.max_pool(x)
				self.net.print_debug("Max pool1:", x.shape)
				
				# Выход: 128, 14, 14
				
				# Сверточный слой 2
				x = F.relu(self.conv2(x))
				self.net.print_debug("Conv2:", x.shape)
				
				# Выход: 64, 14, 14
				
				# Макс пулинг
				x = self.max_pool(x)
				self.net.print_debug("Max pool2:", x.shape)
				
				# Выход: 64, 7, 7
				
				# Выравнивающий слой
				x = x.view(-1, 3136)
				self.net.print_debug("Line:", x.shape)
				
				# Выход: 3136
				
				# Полносвязный слои
				x = self.drop50(x)
				x = F.relu(self.fc1(x))
				x = self.drop50(x)
				x = self.fc2(x)
				
				self.net.print_debug("Output:", x.shape)
				
				return x
		
		self.model = Model(self)
		
		self.optimizer = torch.optim.Adam(self.model.parameters(), lr=3e-4)
		self.loss = nn.CrossEntropyLoss()
		