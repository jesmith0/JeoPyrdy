import pygame, random, pyttsx
import util, state, time

from constants import *

class Game:

	def __init__(self, screen, lib, num_players, pyttsx_engine):
	
		# STATIC VARIABLES
		self.screen = screen
		self.lib = lib
		self.num_players = num_players
		
		# TTS OBJECT
		self.pyttsx_engine = pyttsx_engine
		
		# STATE VARIABLES
		self.state = state.State()
		self.cursor_loc = [0,0]
		self.cur_round = 0
		self.cur_block = self.lib[0][0][0]
		self.cur_bet = 0
		
		# PLAYER OBJECTS
		self.players = util.init_player_objects(self.num_players)
		
		# GENERATE STATIC SURFACES
		self.board_surf = util.generate_board_surface()				# returns a blank board surface
		self.blank_board_surf = util.generate_board_surface()		# returns a blank board surface (kept blank)
		self.cursor_surf = util.generate_cursor_surface()			# returns a cursor surface
		self.value_surf = util.generate_value_surface()				# returns a list of two lists of value surfaces
		self.correct_surf = util.generate_correct_surface()			# returns a surface to choose between 'correct/incorrect'
		
		# SET DAILY DOUBLES
		self.__set_dailydoubles()
		
		# PLAY SOUNDS
		if (SFX_ON):
			THEME_SOUND.play(-1)
			BOARDFILL_SOUND.play()
		
		# INITIAL UPDATE
		self.update()
		
	def tick_game_clock(self, ms): self.state.game_clock += ms
		
	def update(self, input = None):
	
		if input:
			
			# MAIN SCREEN GAME LOGIC
			if self.state.if_state(MAIN_STATE):
			
				# reset buzzed player variable to active player
				if (self.state.count == 0): self.state.buzzed_player = self.state.active_player
				
				if int(input[self.state.active_player][1]) == 1: self.__update_cursor_loc(1)	# up = 1
				elif int(input[self.state.active_player][2]) == 1: self.__update_cursor_loc(2)	# right = 2
				elif int(input[self.state.active_player][3]) == 1: self.__update_cursor_loc(3)	# left = 3
				elif int(input[self.state.active_player][4]) == 1: self.__update_cursor_loc(4)	# down = 4
				
				# set current block to correspond with cursor's position
				self.cur_block = self.lib[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]]
			
			# BET SCREEN MAIN LOGIC
			elif self.state.if_state(BET_STATE):
			
				max_bet = self.players[self.state.active_player].get_max_bet()
			
				# if FINAL JEOPARDY and player has no points to bet
				if self.state.final and self.players[self.state.active_player].score <= 0: self.state.skip_player = True
				else:
					# set maximum bet
					if self.state.count == 0: self.cur_bet = max_bet
					
					# increase/decrease current bet
					if (int(input[self.state.active_player][1]) or int(input[self.state.active_player][2])) and (self.cur_bet + 100 <= max_bet): self.cur_bet += 100
					elif (int(input[self.state.active_player][3]) or int(input[self.state.active_player][4])) and (self.cur_bet - 100 >= 0): self.cur_bet -= 100
			
			# DISPLAY CLUE SCREEN GAME LOGIC
			elif self.state.if_state(SHOW_CLUE_STATE):
			
				buzzed_players = []
			
				# (IF NOT A DAILY DOUBLE) ANY PLAYER MAY BUZZ IN
				if self.state.dailydouble: buzzed_players.append(self.state.active_player)
				else:
					i = 0
					for buzzer in input[:self.num_players]:
						if int(buzzer[0]) == 1: buzzed_players.append(i)
						i += 1
				
				# only if someone has buzzed in
				if len(buzzed_players) > 0:
				
					# choose random player, if both buzzed together
					self.state.set_buzzed_player(buzzed_players[random.randint(0, len(buzzed_players)-1)])
					
					# play 'ring in' sound
					if not self.state.dailydouble: BUZZ_SOUND.play()
			
			# BUZZED-IN SCREEN GAME LOGIC
			elif self.state.if_state(BUZZED_STATE): pass
			
			# DISPLAY RESPONSE SCREEN GAME LOGIC
			elif self.state.if_state(SHOW_RESP_STATE): 
			
				print self.state.count
				if self.state.buzzed_timeout and self.state.count == 0: self.__update_points(False)
			
			# CHECK RESPONSE SCREEN GAME LOGIC
			elif self.state.if_state(CHECK_STATE):
				
				# player indicates CORRECT/INCORRECT
				if int(input[self.state.buzzed_player][3]):
					self.__update_points()
					self.state.active_player = self.state.buzzed_player
					
				elif int(input[self.state.buzzed_player][2]) or self.state.buzzed_timeout:
					self.__update_points(False)
			
			# FINAL JEOPARDY BET SCREEN GAME LOGIC
			elif self.state.if_state(FINAL_BET_STATE):
					
				# process input
				self.__proc_final_input(input)
				
				# check if completed
				completed = True
				for player in self.players:
					if not player.bet_set: completed = False
				
				# on completion, notify state object
				if completed:
					
					self.state.all_bets_set = True
					
					# set up check state
					for player in self.players:		
						print player.cur_bet
						if player.cur_bet <= 0: player.check_set = True
			
			# FINAL JEOPARDY CHECK SCREEN GAME LOGIC
			elif self.state.if_state(FINAL_CHECK_STATE):
					
				# process input
				self.__proc_final_input(input)
				
				for player in self.players:
					print player.cur_bet
				print
				
				# check if completed
				completed = True
				for player in self.players:
					if not player.check_set: completed = False
				
				# on completion, notify state object
				if completed: self.state.all_checks_set = True
				
		# UPDATE GAME STATE
		self.state.update(input, self.cur_block)
		
		# UPDATE ROUND
		self.__update_round()
		
		# DISPLAY GAME STATE
		self.__display_state(self.state.cur_state)
		
		return True
		
	def __proc_final_input(self, input):
	
		for i in range(self.num_players):
		
			player =  self.players[i]
		
			# increment/decrement bet
			if self.state.if_state(FINAL_BET_STATE) and not player.bet_set:
				
				if int(input[i][0]): player.bet_set = True
				elif int(input[i][1]): player.add_to_bet()
				elif int(input[i][4]): player.sub_from_bet()
			
			# indicate correct/incorrect
			if self.state.if_state(FINAL_CHECK_STATE):
			
				if int(input[i][2]):
					player.sub_from_score(player.cur_bet)
					player.check_set = True
					
				elif int(input[i][3]):
					player.add_to_score(player.cur_bet)
					player.check_set = True
		
	def __update_round(self):
	
		# check if round over
		if self.state.check_round and self.__check_round():
		
			# increment round, play sound
			self.cur_round += 1
			if SFX_ON: BOARDFILL_SOUND.play()
			
			# initiate final jeopardy
			if self.cur_round == 2:
			
				self.__init_final()
				
				# set up final bet state
				for player in self.players: player.setup_bet(True)
	
	### DEBUGGING ONLY ###
	def force_update_round(self):
	
		self.__init_final()
				
		# set up final bet state
		for player in self.players: player.setup_bet(True)
		
	def __display_state(self, cur_state):
	
		# call appropriate display function based on the current state
		if cur_state == MAIN_STATE: 			self.__display_main()
		elif cur_state == SHOW_CLUE_STATE: 		self.__display_clue_resp()			
		elif cur_state == BUZZED_STATE: 		self.__display_clue_resp()
		elif cur_state == SHOW_RESP_STATE: 		self.__display_clue_resp()
		elif cur_state == CHECK_STATE and not self.state.buzzed_timeout: self.__display_check()
		elif cur_state == BET_STATE and not self.state.final: self.screen.blit(util.generate_bet_surface(self.cur_block.category, self.players[self.state.buzzed_player], self.cur_bet), (0, 0))
		elif cur_state == BET_STATE and self.state.final: self.screen.blit(util.generate_bet_surface(self.cur_block.category, self.players[self.state.active_player], self.cur_bet, True), (0, 0))
		elif cur_state == FINAL_BET_STATE:		self.__display_final_bet()
		elif cur_state == FINAL_CHECK_STATE: 	self.__display_final_check()
		elif cur_state == END_STATE: 			self.__display_end()
		
	# UPDATES CLUES AND CATEGORIES AND CURSOR ON BOARD SURFACE
	def __update_board_surf(self):
	
		width_interval = BOARD_SIZE[0]/6
		height_interval = BOARD_SIZE[1]/6
	
		# blit board surface with blank board
		self.board_surf.blit(self.blank_board_surf, (0,0))
		
		# blit cursor to board
		self.board_surf.blit(self.cursor_surf, (self.cursor_loc[0]*width_interval,(self.cursor_loc[1]+1)*height_interval))
	
		# blit board surface with values
		i = 0
		for category in self.lib[self.cur_round]:
		
			self.board_surf.blit(self.lib[self.cur_round][i][0].cat_board_surface(), (i*width_interval+10,-10))
		
			j = 0
			for block in category:
				if not block.clue.completed:
				
					self.board_surf.blit(self.value_surf[self.cur_round][j], (i*width_interval+10, (j+1)*height_interval+10))
				
				j += 1
			i += 1

	# BLIT CLUE/RESPONSE DISPLAY TO SCREEN
	def __display_clue_resp(self):
	
		self.screen.fill(BLUE)
		
		clue_surf = util.generate_text_surface((str(self.cur_block.category).upper()))
	
		# if clue display
		if self.state.if_state(SHOW_CLUE_STATE):
			char_surf = ALEX_IMAGE
			text_surf = util.generate_text_surface(self.cur_block.clue)
			tts = self.cur_block.clue
		elif self.state.if_state(BUZZED_STATE):
			char_surf = self.players[self.state.buzzed_player].char_surface
			text_surf = util.generate_text_surface(self.cur_block.clue)
			tts = self.cur_block.clue
		elif self.state.if_state(SHOW_RESP_STATE):
			char_surf = self.players[self.state.buzzed_player].char_surface
			text_surf = util.generate_text_surface(self.cur_block.response)
			tts = self.cur_block.response
		
		# scale character surface
		scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3))
		
		# blit character and text to screen
		util.blit_alpha(self.screen, scaled_image, (0, DISPLAY_RES[1]-scaled_image.get_height()), 100)
		self.screen.blit(char_surf, (0, DISPLAY_RES[1]-char_surf.get_height()))
		self.screen.blit(clue_surf, (DISPLAY_RES[0]/2 - BOARD_SIZE[0]/2, -200))
		self.screen.blit(text_surf, (DISPLAY_RES[0]/2 - BOARD_SIZE[0]/2,0))
		
		# read clue/response
		if (self.state.if_state(SHOW_CLUE_STATE) or self.state.if_state(SHOW_RESP_STATE) or (self.state.if_state(BUZZED_STATE) and self.state.dailydouble)) and (self.state.count == 0):
			try: self.pyttsx_engine.say(str(tts).decode('utf-8'))
			except UnicodeDecodeError: self.pyttsx_engine.say('Unicode Decode Error')
			except: self.pyttsx_engine.say('Unknown Error')
	
	# BLIT MAIN DISPLAY TO SCREEN
	def __display_main(self):
	
		self.screen.fill(BLUE)
		self.__update_board_surf()
		
		# create scaled character surface
		active_char_surf = self.players[self.state.active_player].char_surface
		scaled_image = pygame.transform.scale(active_char_surf, (active_char_surf.get_width()*3, active_char_surf.get_height()*3))
		
		# blit active char
		util.blit_alpha(self.screen, scaled_image, (0, DISPLAY_RES[1]-scaled_image.get_height()), 100)
		
		# blit game board
		self.screen.blit(self.board_surf, (DISPLAY_RES[0]/2-BOARD_SIZE[0]/2,0))
		
		# blit all characters
		self.__blit_all_characters(self.screen)
	
	# BLIT CHECK RESPONSE DISPLAY TO SCREEN
	# correct = 0, incorrect = 1
	def __display_check(self):

		char_surf = self.players[self.state.buzzed_player].char_surface
		scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3))
		
		self.screen.fill(BLUE)
		
		util.blit_alpha(self.screen, scaled_image, (0, DISPLAY_RES[1]-scaled_image.get_height()), 100)
		self.screen.blit(char_surf, (0, DISPLAY_RES[1]-char_surf.get_height()))
		
		self.screen.blit(self.correct_surf, (DISPLAY_RES[0]/2-BOARD_SIZE[0]/2,0))
		
	def __display_final_bet(self):
	
		# blit background image
		background_surf = pygame.transform.scale(FJBG_IMAGE, DISPLAY_RES)
		self.screen.blit(background_surf, (0, 0))
		
		# blit all characters
		self.__blit_all_characters(self.screen)
		
	def __display_final_check(self):
	
		main_center_loc = [BOARD_SIZE[0]/2, BOARD_SIZE[1]/2]
	
		correct_text_surf = util.generate_text_surface("CORRECT")
		incorrect_text_surf = util.generate_text_surface("INCORRECT")
		
		orange_rect_surf = pygame.Surface((100, 50)).convert()
		orange_rect_surf.fill(ORANGE)
		
		green_rect_surf = pygame.Surface((100, 50)).convert()
		green_rect_surf.fill(GREEN)
	
		# fill screen
		self.screen.fill(BLUE)
		
		# blit response
		self.screen.blit(util.generate_text_surface(self.cur_block.response), (DISPLAY_RES[0]/2 - BOARD_SIZE[0]/2,0))
		
		self.screen.blit(orange_rect_surf, (main_center_loc[0]-100, main_center_loc[1]-50))
		self.screen.blit(green_rect_surf, (main_center_loc[0]-100, main_center_loc[1]+50))
		self.screen.blit(correct_text_surf, (100, 80))
		self.screen.blit(incorrect_text_surf, (100, -20))
		
		# blit all characters
		self.__blit_all_characters(self.screen)
		
	def __display_end(self):
	
		# scale and blit background image
		background_surf = pygame.transform.scale(MAINBG_IMAGE, DISPLAY_RES)
		self.screen.blit(background_surf, (0, 0))
		
		# determine winners (may be a tie)
		winners = self.__determine_winners()
		
		# blit winners
		for i in range(len(winners)):
			char_surf = winners[i].char_surface
			self.screen.blit(pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3)), (i*300, 100))
		
		self.screen.blit(util.generate_text_surface("CONGRATULATIONS!!!"), (0,-200))
		
	def __determine_winners(self):
	
		winners = [self.players[0]]
		for player in self.players[1:]:
			if player.score > winners[0].score: winners = [player]
			elif player.score == winners[0].score: winners.append(player)
			
		return winners
		
	def __blit_all_characters(self, screen):
	
		char_surfs = []
		
		# generate character surfaces
		for i in range(self.num_players):
			char_surfs.append(self.players[i].char_surface)
		
		# width interval dependant on number of players
		width_interval = DISPLAY_RES[0]/self.num_players
		
		blit_loc = (((width_interval*(i)) + width_interval/2) - char_surfs[i].get_width()/2, DISPLAY_RES[1]-char_surfs[i].get_height())
		
		# blit all characters
		for i in range(self.num_players):
		
			# calculate location
			blit_loc = (((width_interval*(i)) + width_interval/2) - char_surfs[i].get_width()/2, DISPLAY_RES[1]-char_surfs[i].get_height())
			
			if (self.state.if_state(FINAL_BET_STATE) and self.players[i].bet_set) or (self.state.if_state(FINAL_CHECK_STATE) and self.players[i].check_set):
				util.blit_alpha(screen, char_surfs[i], blit_loc, 25)
				
			else: screen.blit(char_surfs[i], blit_loc)
	
	# UPDATE CURSON BASED ON BUTTON DIRECTION
	def __update_cursor_loc(self, direction):
	
		# up
		if direction == 1:		
			if self.cursor_loc[1] > 0: self.cursor_loc[1] -= 1
			else: self.cursor_loc[1] = 4
		
		# right
		elif direction == 2:
			if self.cursor_loc[0] < 5: self.cursor_loc[0] += 1
			else: self.cursor_loc[0] = 0
		
		# left
		elif direction == 3:
			if self.cursor_loc[0] > 0: self.cursor_loc[0] -= 1
			else: self.cursor_loc[0] = 5
		
		# down
		elif direction == 4:
			if self.cursor_loc[1] < 4: self.cursor_loc[1] += 1
			else: self.cursor_loc[1] = 0
				
	def __set_dailydoubles(self):
	
		# for both rounds
		for round in self.lib[:-1]:
		
			# choose random locations
			dd1 = [random.randint(0, 5), random.randint(0, 4)]
			dd2 = [random.randint(0, 5), random.randint(0, 4)]
			
			# asserts that locations are different
			while (dd1[0] == dd2[0]): dd2[0] = random.randint(0, 5)
			
			# set daily double
			round[dd1[0]][dd1[1]].set_dailydouble(True)
			round[dd2[0]][dd2[1]].set_dailydouble(True)
	
	# check to see if current round is over
	def __check_round(self):
	
		for category in self.lib[self.cur_round]:
			for block in category:
				if not block.clue_completed(): return False
		
		return True
	
	# by default ADD points
	def __update_points(self, add = True):
	
		# determine points to add/sub
		if self.state.dailydouble or self.state.final: points = self.cur_bet
		else: points = POINT_VALUES[self.cur_round][self.cursor_loc[1]]
	
		if add:
			self.players[self.state.buzzed_player].add_to_score(points)
		else:
			self.players[self.state.buzzed_player].sub_from_score(points)
			WRONG_SOUNDS[self.state.buzzed_player].play()
			
	def __init_final(self):
	
		# set-up state object
		self.state.set_final_jeopardy()
		
		# set current block to final jeopardy block
		self.cur_block = self.lib[2][0][0]
		self.cur_bet = self.players[self.state.active_player].get_max_bet()