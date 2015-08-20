import util, constants, pygame

class Block:

	def __init__(self, category, clue, response):
	
		self.category = category
		self.clue = clue
		self.response = response
		
	def cat_board_surface(self): return self.category.board_surface
	
	def cat_display_surface(self): return self.category.display_surface
		
	def category_completed(self): return self.category.completed
		
	def clue_completed(self): return self.clue.completed
	
	def set_dailydouble(self, bool): self.clue.dailydouble = True
		
	def is_dailydouble(self): return self.clue.dailydouble
	
	def see_clue(self): self.clue.completed = True
	
	def complete_category(self): self.category.completed = True

class Category:

	def __init__(self, text):
	
		# data
		self.text = text
		self.board_surface = None
		self.display_surface = None
		
		# state
		self.completed = False
		
		self.board_surface = util.generate_text_surface(self.text, constants.BOARD_SIZE[0]/6 - 20, constants.BOARD_SIZE[0]/6 - 20, 20, constants.YELLOW, "helvetica", constants.DARK_BLUE)
		
	def __str__(self): return self.text

class Clue:

	def __init__(self, text, dailydouble = False):
	
		# data
		self.text = text
		self.surface = None
		
		# state
		self.completed = False
		self.dailydouble = dailydouble
		
		# CALL TO __generate_surface()
		
	def __str__(self): return self.text
		
class Response:

	def __init__(self, text):
	
		# data
		self.text = text
		self.surface = None
		
		# CALL TO __generate_surface()
		
	def __str__(self): return self.text