#!/usr/bin/env python3

## Python built-in imports
import sys, os
from itertools import combinations
from subprocess import Popen, PIPE
## External imports
import pycosat

## Color printing
COLORS = ['\33[30m', '\33[31m', '\33[32m', '\33[33m', '\33[34m', '\33[35m','\33[36m', '\33[37m', '\33[90m', '\33[91m', '\33[92m', '\33[93m', '\33[94m', '\33[95m', '\33[96m', '\33[97m']
CEND = '\33[0m'

class FlowFormatError(Exception):
	pass

class FlowSAT:
	def __init__(self, k, grid, endpoints = None, bridges = None, color_to_num = None):
		## Take user input arguments and setup attributes
		self.m = len(grid)
		self.n = len(grid[0])
		self.k = k
		self.grid = grid
		if bridges is not None:
			self.bridges = bridges
		else:
			self.bridges = []
		if endpoints is not None:
			self.endpoints = endpoints
		else:
			self.endpoints = {}
			for i in range(k):
				self.endpoints[i] = []
			for i in range(n):
				for j in range(n):
					if grid[i][j] is not None and grid[i][j] != '+':
						color = grid[i][j]
						self.endpoints[color].append((i, j))
		if color_to_num is not None:
			self.color_to_num = color_to_num
			self.num_to_color = {}
			for key, value in color_to_num.items():
				self.num_to_color[value] = key
		else:
			self.color_to_num = None
			self.num_to_color = None
		# Initialize the SAT clauses
		self.clauses = []

	@classmethod
	def from_file(cls, filename):
		# Open up file for reading only
		file = open(filename, "r")
		m = 0 # Number of rows
		n = None # Number of columns
		colors = set()
		endpoints = {}
		endpoint_counter = {}
		color_to_num = {}
		grid = []
		bridges = []
		for i, line in enumerate(file):
			m += 1
			grid_line = []
			for j, c in enumerate(line.strip()):
				# Check/set n value
				if n is None:
					n = len(line.strip())
				else:
					if n != len(line.strip()):
						raise FlowFormatError("The lines in the file do not have the same length! Unable to parse file!")
				# Check what is in the grid
				if c == "*":
					# Empty spot
					grid_line.append(None)
				elif c == "+":
					# Bridge
					grid_line.append("+")
					bridges.append((i, j))
				else:
					# Endpoint
					color = int(c, base=16)
					color_to_num[c] = color
					colors.add(color)
					grid_line.append(color)
					if color not in endpoints:
						endpoints[color] = [(i, j)]
						endpoint_counter[color] = 1
					else:
						endpoints[color].append((i, j))
						endpoint_counter[color] += 1
			grid.append(grid_line)
		# Check that there are 2 endpoints for each color
		for color in colors:
			if endpoint_counter[color] != 2:
				raise FlowFormatError("Invalid number of endpoints for color = %d! Found %d endpoints, but there should only be 2!" % (color, endpoint_counter[color]))
		solver = FlowSAT(len(colors), grid, endpoints, bridges, color_to_num)
		return solver

	@classmethod
	def from_user_input(cls):
		sys.stdout.flush()
		## Get k
		k = input("How many colors/flows are there (k)? >> ")
		while not k.isdigit():
			print("Invalid input! k must be an integer!")
			k = input("How many colors/flows are there (k)? >> ")
		k = int(k)
		## Get m (number of rows)
		m = input("How many rows are in this puzzle (m)? >> ")
		while not m.isdigit():
			print("Invalid input! m must be an integer!")
			k = input("How many rows are in this puzzle (m)? >> ")
		m = int(m)
		## Get n (number of columns)
		## does not have to be the same as m => rectangle puzzles!
		n = input("How many columns are in this puzzle (n)? >> ")
		while not n.isdigit():
			print("Invalid input! n must be an integer!")
			k = input("How many columns are in this puzzle (n)? >> ")
		n = int(n)
		## Directions and input
		print("Directions:")
		print("For each line, a single character for each square in the puzzle grid.")
		print("If the square is an endpoint, use a character (e.g., the first letter of the color's name) \
			to denote that color. Make sure to use the same color for the second endpoint of the same color, \
			otherwise the file cannot be parsed correctly. Do NOT use one of the reserved characters: '*', '+'")
		print("If the square is an empty square, enter the character '*' (without quotes).")
		print("If the square is a bridge, enter the character '+' (without quotes).")
		print()
		## Start reading input and checking for errors
		color_to_num = {}
		n_colors = 0
		grid = []
		bridges = []
		endpoints = {}
		endpoint_counter = {}
		for i in range(m):
			line_str = input("Input line %d: " % (i+1))
			if len(line_str) != n:
				raise FlowFormatError("Invalid number of characters in a line! Got %d characters but expected %d!" % (len(line_str), n))
			grid_line = []
			for j, c in enumerate(line_str):
				if c == "*":
					# Empty square
					grid_line.append(None)
				elif c == "+":
					# Bridge
					grid_line.append("+")
					bridges.append((i, j))
				else:
					if c not in color_to_num:
						color_to_num[c] = n_colors
						endpoint_counter[n_colors] = 1
						endpoints[n_colors] = [(i, j)]
						grid_line.append(n_colors)
						n_colors += 1
					else:
						this_color = color_to_num[c]
						endpoint_counter[this_color] += 1
						if endpoint_counter[this_color] > 2:
							raise FlowFormatError("There cannot be more than 2 endpoints of the same color!")
						endpoints[this_color].append((i, j))
						grid_line.append(this_color)
			grid.append(grid_line)
		# Check to see if the correct number of colors were used
		if k != n_colors:
			raise FlowFormatError("Incorrect number of colors used! Found %d colors but initial input indicated there would be %d colors!" % (n_colors, k))
		# Check that there are two endpoints for each color
		for color in range(k):
			if endpoint_counter[color] != 2:
				raise FlowFormatError("Invalid number of endpoints per color!")
		solver = FlowSAT(k, grid, endpoints, bridges, color_to_num)
		return solver

	def var_num(self, row, column, color):
		num = 1 + row*self.n + column + (color*self.n*self.n)
		return num

	def var_num_inv(self, num):
		num -= 1
		color = num // (self.n * self.n)
		num -= (color*self.n*self.n)
		row = num//self.n
		num -= row*self.n
		column = num
		return (row, column, color)

	def legal_neighbors(self, point):
		neighbors = []
		row, col = point
		if row-1 >= 0: #and (row-1, col) not in self.endpoints:
			neighbors.append((row-1, col))
		if row+1 < self.n: #and (row+1, col) not in self.endpoints:
			neighbors.append((row+1, col))
		if col-1 >= 0: #and (row, col-1) not in self.endpoints:
			neighbors.append((row, col-1))
		if col+1 < self.n: #and (row, col+1) not in self.endpoints:
			neighbors.append((row, col+1))
		return neighbors

	def add_endpoint_clauses(self):
		all_colors = set(range(self.k))
		for color in range(self.k):
			endpoints = self.endpoints[color]
			for p in endpoints:
				## Clause that endpoint is its own color
				color_var = self.var_num(p[0], p[1], color)
				self.clauses.append([color_var])
				## Clauses that endpoint is not any of the other colors
				for other_color in all_colors - set([color]):
					other_color_var = self.var_num(p[0], p[1], other_color)
					self.clauses.append([-other_color_var])
				## Clauses so that exactly one adjacent connecting point is
				## the same color as the endpoint
				neighbors = self.legal_neighbors(p)
				neighbor_vars = [self.var_num(neighbor[0], neighbor[1], color) for neighbor in neighbors]
				# At least one is true
				at_least_one = [v for v in neighbor_vars]
				self.clauses.append(at_least_one)
				# At most one is true
				for i in range(len(neighbor_vars)-1):
					for j in range(i+1, len(neighbor_vars)):
						clause = [-neighbor_vars[i], -neighbor_vars[j]]
						self.clauses.append(clause)

	def add_connecting_point_clauses(self):
		## Exactly two adjacent points with same color
		for i, row in enumerate(self.grid):
			for j, item in enumerate(row):
				if item is None:
					point = (i, j)
					for color in range(self.k):
						self.add_neighbor_clauses_with_color(point, color)

	def add_neighbor_clauses_with_color(self, point, color):
		neighbors = self.legal_neighbors(point)
		neighbor_vars = [self.var_num(neighbor[0], neighbor[1], color) for neighbor in neighbors]
		point_color = self.var_num(point[0], point[1], color)
		if len(neighbor_vars) == 2:
			self.clauses.append([-point_color, neighbor_vars[0]])
			self.clauses.append([-point_color, neighbor_vars[1]])
		elif len(neighbor_vars) == 3:
			self.clauses.append([-point_color, neighbor_vars[0], neighbor_vars[1]])
			self.clauses.append([-point_color, neighbor_vars[0], neighbor_vars[2]])
			self.clauses.append([-point_color, neighbor_vars[1], neighbor_vars[2]])
			self.clauses.append([-point_color, -neighbor_vars[0], -neighbor_vars[1], -neighbor_vars[2]])
		elif len(neighbor_vars) == 4:
			self.clauses.append([-point_color, neighbor_vars[0], neighbor_vars[1], neighbor_vars[2]])
			self.clauses.append([-point_color, neighbor_vars[0], neighbor_vars[1], neighbor_vars[3]])
			self.clauses.append([-point_color, neighbor_vars[0], neighbor_vars[2], neighbor_vars[3]])
			self.clauses.append([-point_color, neighbor_vars[1], neighbor_vars[2], neighbor_vars[3]])
			self.clauses.append([-point_color, -neighbor_vars[0], -neighbor_vars[1], -neighbor_vars[2]])
			self.clauses.append([-point_color, -neighbor_vars[0], -neighbor_vars[1], -neighbor_vars[3]])
			self.clauses.append([-point_color, -neighbor_vars[0], -neighbor_vars[2], -neighbor_vars[3]])
			self.clauses.append([-point_color, -neighbor_vars[1], -neighbor_vars[2], -neighbor_vars[3]])			
		else:
			print("Unexpected number of neighbors: %d" % len(neighbor_vars))

	def add_bridge_clauses(self):
		for i, row in enumerate(self.grid):
			for j, item in enumerate(row):
				if item == "+":
					point = (i, j)
					## Bridge should have exactly 2 colors associated with it
					point_color_vars = [self.var_num(i, j, color) for color in range(self.k)]
					# At most 2
					for combo in combinations(point_color_vars, 3):
						clause = [-var for var in combo]
						self.clauses.append(clause)
					# At least 2
					for combo in combinations(point_color_vars, len(point_color_vars)-1):
						clause = list(combo)
						self.clauses.append(clause)
					## Bridge should be connected to 2 points of each color on opposite sides
					## TODO: make custom method for bridges, but see how this works for now,
					## 			maybe it will work since bridge will have two colors? But
					## 			this won't enforce the sides the colors are on...
					for color in range(self.k):
						self.add_neighbor_clauses_with_color(point, color)

	def add_no_cycle_clauses(self):
		## TODO
		## Theoretically, it seems necessary
		## In practice, it hasn't been necessary
		pass

	def all_connecting_points_have_one_color(self):
		for i, row in enumerate(self.grid):
			for j, item in enumerate(row):
				if item is None:
					point = (i, j)
					point_color_vars = []
					for color in range(self.k):
						point_color_vars.append(self.var_num(i, j, color))
					#print("point_color_vars:", point_color_vars)
					at_least_one = [*point_color_vars]
					self.clauses.append(at_least_one)
					for a in range(self.k - 1):
						for b in range(a+1, self.k):
							self.clauses.append([-point_color_vars[a], -point_color_vars[b]])
							#print([-point_color_vars[a], -point_color_vars[b]])

	def grid_from_solution(self, solution):
		grid = [[None for _ in range(self.n)] for _ in range(self.n)]
		for var in solution:
			if var > 0:
				row, column, color = self.var_num_inv(var)
				grid[row][column] = color
		for point in self.bridges:
			row, col = point
			grid[row][col] = "+"
		return grid

	def print_grid(self, grid):
		print()
		for row in grid:
			new_row = []
			for item in row:
				if isinstance(item, int):
					cell = COLORS[item] + self.num_to_color[item] + CEND
					new_row.append(cell)
				elif item == "+":
					new_row.append(item)
			print("".join(new_row))
		print()

	def solve(self):
		## Setup SAT clauses
		self.add_endpoint_clauses()
		self.all_connecting_points_have_one_color()
		self.add_connecting_point_clauses()
		self.add_bridge_clauses()

		## Get SAT solution
		solution = pycosat.solve(self.clauses)
		# Check if there is no solution
		if not isinstance(solution, list):
			return False
		## Convert solution into a grid
		new_grid = self.grid_from_solution(solution)
		self.print_grid(new_grid)
		return True

## Utility functions

def prompt_user_yn(prompt, default = "Y"):
	valid_responses = ["y", "yes", "n", "no", ""]
	if default == "Y":
		response_str = "(Y/n)"
	else:
		response_str = "(y/N)"
	response = input(prompt + " " + response_str + " >> ").lower()
	while response not in valid_responses:
		print("Invalid response!")
		response = input(prompt + " " + response_str + " >> ").lower()
	if not response:
		if default == "Y":
			return True
		else:
			return False
	elif response == "y" or response == "yes":
		return True
	else:
		return False

def main():
	"""
	@brief      Driver function - Runs the Flow Solver program
	
	"""
	## Get TTY size
	tty_size_proc = Popen(['stty', 'size'], stdout = PIPE)
	tty_height, tty_width = map(int, tty_size_proc.communicate()[0].strip().split())

	## Banner
	print("~"*tty_width)
	print("~"*((tty_width-len('Flow Solver'))//2) + "Flow Solver" + "~"*((tty_width-len('Flow Solver'))//2))
	print("~"*tty_width)
	print()
	
	## Main loop
	finished = False
	while not finished:
		try:
			read_from_file = prompt_user_yn("Would you like to read a Flow puzzle from file?")
			if read_from_file:
				## Read from file
				file_name = input("Please enter the file name to be read: ")
				# Check that file exists
				while not os.path.isfile(file_name):
					print("File %s does not exist! Please check file name and make sure the correct directory is specified" % file_name)
					file_name = input("Please enter the file name to be read: ")
				# Try to read the file
				# if parsing fails, from_file will throw a FlowFormatError exception,
				# the particular error will be displayed, and the loop will start over.
				try:
					solver = FlowSAT.from_file(file_name)
				except FlowFormatError as e:
					print(e)
					continue
			else:
				# Read line by line
				try:
					solver = FlowSAT.from_user_input()
				except FlowFormatError as e:
					print(e)
					continue
			# Solve the puzzle!
			success = solver.solve()
			if not success:
				print("The puzzle could not be solved! Perhaps the entered puzzle is not solvable? Please check your input again.")
			# Continue or end session?
			finished = not prompt_user_yn("Would you like to try another Flow puzzle?")				
		except (KeyboardInterrupt, EOFError):
			finished = prompt_user_yn("\nAre you sure you would like to exit?")

	print("Goodbye!")

if __name__ == '__main__':
	main()