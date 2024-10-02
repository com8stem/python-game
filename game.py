import pygame
import random
import sys
import os
import math

# 定数マクロの定義

# 画面のサイズ
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 1000

# パドルのサイズと速度
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 15

# ボールのサイズと速度
BALL_SIZE = 20
BALL_SPEED_X = 3
BALL_SPEED_Y = -3

# ブロックのサイズと配置
BLOCK_WIDTH = 80
BLOCK_HEIGHT = 30
NUM_BLOCKS = 40
BLOCKS_OFFSET = 10

# 色の定義
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 0, 139)
GREEN = (0, 255, 0)
LIGHT_GREEN = (144, 238, 144)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
PINK = (255, 192, 203)

# コンボ用のグローバル変数とマクロ
combo = 0
combo_timer = 0
COMBO_TIME = 1000  # コンボ継続時間（ミリ秒）

# パドルクラス
class Paddle(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()
		self.original_image = pygame.Surface([PADDLE_WIDTH, PADDLE_HEIGHT])  # 元のパドル画像を保持
		self.original_image.fill(LIGHT_BLUE)
		self.image = self.original_image.copy()
		self.rect = self.image.get_rect()
		self.rect.x = (SCREEN_WIDTH - PADDLE_WIDTH) // 2
		self.rect.y = SCREEN_HEIGHT - 2 * PADDLE_HEIGHT
		self.moving_left = False
		self.moving_right = False

	def move_left(self):
		self.rect.x -= PADDLE_SPEED
		if self.rect.x < 0:
			self.rect.x = 0

	def move_right(self):
		self.rect.x += PADDLE_SPEED
		if self.rect.x > SCREEN_WIDTH - self.rect.width:
			self.rect.x = SCREEN_WIDTH - self.rect.width

	def update(self):
		keys = pygame.key.get_pressed()
		if keys[pygame.K_LEFT]:
			self.move_left()
		if keys[pygame.K_RIGHT]:
			self.move_right()

		self.image = pygame.transform.scale(self.original_image, (self.rect.width, self.rect.height))


# ボールクラス
class Ball(pygame.sprite.Sprite):
	def __init__(self, paddle, stage, is_original=True):
		super().__init__()
		self.image = pygame.Surface([BALL_SIZE, BALL_SIZE])
		self.color = GREEN if is_original else LIGHT_GREEN
		self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.centerx = paddle.rect.centerx
		self.rect.bottom = paddle.rect.top
		self.speed_x = BALL_SPEED_X + stage
		self.speed_y = 0
		self.launched = False
		self.last_hit_time = 0
		self.is_original = is_original

	def update(self):
		current_time = pygame.time.get_ticks()
		if self.launched:
			self.rect.x += self.speed_x
			self.rect.y += self.speed_y
			max_angle = math.pi / 3 
			min_angle = math.pi / 18
			current_angle = math.atan2(abs(self.speed_y), abs(self.speed_x))
			if current_angle < min_angle:  # 10度未満の場合
				sign_y = 1 if self.speed_y >= 0 else -1
				speed = math.sqrt(self.speed_x ** 2 + self.speed_y ** 2)
				self.speed_y = sign_y * speed * math.sin(min_angle)
				self.speed_x = math.copysign(math.sqrt(speed**2 - self.speed_y**2), self.speed_x)
			if self.rect.x <= 0 or self.rect.x >= SCREEN_WIDTH - BALL_SIZE:
				self.speed_x = -self.speed_x
			if self.rect.y <= 0:
				self.speed_y = -self.speed_y
			if self.rect.top > SCREEN_HEIGHT:
				self.kill()  # ボールが画面下に出たら削除
			if current_time - self.last_hit_time > COMBO_TIME:
				combo = 0
				combo_timer = 0

	def launch(self):
		self.launched = True
		self.speed_y = -(BALL_SPEED_Y + stage)

# Blockクラス
class Block(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface([BLOCK_WIDTH, BLOCK_HEIGHT])
		self.image.fill(WHITE)
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.item_type = random.choices([None, PowerUp, SpeedDown, MultiBall, ExtraLife], weights=[65, 10, 10, 10, 5])[0]

# アイテムクラス
class Item(pygame.sprite.Sprite):
	def __init__(self, x, y, color):
		super().__init__()
		self.image = pygame.Surface([20, 20])
		self.image.fill(color)
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.speed_y = 3

	def update(self):
		self.rect.y += self.speed_y
		if self.rect.y > SCREEN_HEIGHT:
			self.kill()

# パワーアップアイテムクラス
class PowerUp(Item):
	def __init__(self, x, y):
		super().__init__(x, y, RED)

# スピードダウンアイテムクラス
class SpeedDown(Item):
	def __init__(self, x, y):
		super().__init__(x, y, YELLOW)

# マルチボールアイテムクラス
class MultiBall(Item):
	def __init__(self, x, y):
		super().__init__(x, y, PURPLE)

# ライフ回復アイテムクラス
class ExtraLife(Item):
	def __init__(self, x, y):
		super().__init__(x, y, PINK)

# ゲームのリセット関数
def reset_game(stage):
	global score, balls, paddle, blocks, items, all_sprites, lives
	score = 0
	lives = 3
	all_sprites = pygame.sprite.Group()
	blocks = pygame.sprite.Group()
	balls = pygame.sprite.Group()
	items = pygame.sprite.Group()
	
	paddle = Paddle()
	all_sprites.add(paddle)

	ball = Ball(paddle, stage, is_original=True)
	all_sprites.add(ball)
	balls.add(ball) 

	# ブロックの配置をランダムにする
	available_positions = []
	for x in range(0, SCREEN_WIDTH - BLOCK_WIDTH + 1, BLOCK_WIDTH + BLOCKS_OFFSET):
		for y in range(50 + (stage * 100), 350 + (stage * 100), BLOCK_HEIGHT + BLOCKS_OFFSET):
			available_positions.append((x, y))
	random.shuffle(available_positions)

	for i in range(NUM_BLOCKS):
		if i < len(available_positions):
			x, y = available_positions[i]
			block = Block(x, y)
			blocks.add(block)
			all_sprites.add(block)

# ボタン描画関数
def draw_button(screen, text, center_x, center_y):
	button_font = pygame.font.Font(None, 48)
	button_text = button_font.render(text, True, DARK_BLUE)
	button_rect = button_text.get_rect(center=(center_x, center_y))
	pygame.draw.rect(screen, LIGHT_BLUE, button_rect.inflate(20, 20))
	screen.blit(button_text, button_rect)

# スタート画面の関数
def show_start_screen():
	start_screen = True
	while start_screen:
		screen.fill(DARK_BLUE)
		
		title_font = pygame.font.Font(None, 72)
		instruction_font = pygame.font.Font(None, 36)
		
		title_text = title_font.render("Block Breaker", True, WHITE)
		title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
		screen.blit(title_text, title_rect)
		
		instructions = [
			"Press Enter to Start",
			"",
			"Move the paddle: <- or ->",
			"",
			"Launch the ball: Space",
			"",
			"Pause: P",
			"",
			"Quit game: Q"
		]
		
		for i, instruction in enumerate(instructions):
			text = instruction_font.render(instruction, True, LIGHT_BLUE)
			text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 50))
			screen.blit(text, text_rect)
		
		start_text = instruction_font.render("Press Enter to Start", True, GREEN)
		start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
		screen.blit(start_text, start_rect)
		
		pygame.display.flip()

		for event in pygame.event.get():
			if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
				pygame.quit()
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_RETURN:
					start_screen = False

def show_pause_screen():
	while True:
		screen.fill(DARK_BLUE)
		draw_button(screen, "Paused (Press P to resume)", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
		pygame.display.flip()

		for event in pygame.event.get():
			if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
				pygame.quit()
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_p:
					return


def show_stage_clear_screen(stage):
	while True:
		screen.fill(DARK_BLUE)
		draw_button(screen, f"Stage {stage - 1} Clear! (Press Enter to continue)", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
		pygame.display.flip()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_RETURN:
					return


def show_game_over_screen(score):
	while True:
		screen.fill(DARK_BLUE)
		game_over_text = FONT.render("Game Over", True, WHITE)
		final_score_text = FONT.render(f"Final Score: {score}", True, WHITE)
		retry_text = FONT.render("Press ESC to retry", True, WHITE)
		screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2))
		screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2 + final_score_text.get_height()))
		screen.blit(retry_text, (SCREEN_WIDTH // 2 - retry_text.get_width() // 2, SCREEN_HEIGHT // 2 + retry_text.get_height() * 2))
		pygame.display.flip()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					return


# ゲームの初期化
pygame.init()

# フォントモジュールの初期化
pygame.font.init()

# 画面の設定
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Block Breaker")

# フォントの設定(pathが含まれるため提出のために一部削除)
FONT = pygame.font.Font(None, 36)

# スタート画面の表示
show_start_screen()

# global変数の初期化
stage = 1
balls = pygame.sprite.Group()
paddle = None
blocks = pygame.sprite.Group()
items = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
lives = 3
score = 0

reset_game(stage)

# ハイスコアの読み込み
high_score = 0
if os.path.exists("highscore.txt"):
	with open("highscore.txt", "r") as file:
		high_score = int(file.read().strip())

# ゲームのメインループ
clock = pygame.time.Clock()
game_over = False
while True:
	paused = False
	for event in pygame.event.get():
		if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
			pygame.quit()
			sys.exit()
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_SPACE:
				for ball in balls:
					if not ball.launched:
						ball.launch()
			elif event.key == pygame.K_p:
				paused = True
				show_pause_screen()

	if paused:
		continue

	# コンボ表示の更新
	if combo_timer > 0:
		combo_timer -= clock.get_time()
		if combo_timer <= 0:
			combo = 0

	all_sprites.update()
	balls.update()

	# 衝突検出
	for ball in balls:
		if pygame.sprite.collide_rect(ball, paddle):
			# ボールの速度の大きさを計算
			speed = math.sqrt(ball.speed_x ** 2 + ball.speed_y ** 2)
			
			# パドルの中央からの相対位置を計算
			relative_intersect_x = ball.rect.centerx - paddle.rect.centerx
			normalized_relative_intersect_x = (relative_intersect_x / (PADDLE_WIDTH / 2))
			
			# 最大角度を設定し、相対位置に基づいて角度を計算
			max_angle = 60
			bounce_angle = normalized_relative_intersect_x * max_angle
			
			# 角度に基づいて新しい速度を設定
			ball.speed_x = speed * math.sin(math.radians(bounce_angle))
			ball.speed_y = -abs(speed * math.cos(math.radians(bounce_angle)))  # 常に上方向に向かうように設定
			
			# 最小速度を設定して、速度が非常に小さくなるのを防ぐ
			min_speed = 3 
			if abs(ball.speed_x) < min_speed:
				ball.speed_x = min_speed if ball.speed_x > 0 else -min_speed
			if abs(ball.speed_y) < min_speed:
				ball.speed_y = -min_speed  # 常に上方向に向かうように設定
			
			# ボールの位置をパドルの上に設定（少しだけ上にずらす）
			ball.rect.bottom = paddle.rect.top - 1
			
		# ブロック衝突処理
		block_collisions = pygame.sprite.spritecollide(ball, blocks, True)
		for block in block_collisions:
			ball.speed_y = -ball.speed_y

			# コンボ処理
			current_time = pygame.time.get_ticks()
			if current_time - ball.last_hit_time <= COMBO_TIME:
				combo += 1
			else:
				combo = 1			
			combo_score = 10 * (combo + 1) * stage
			score += combo_score
			ball.last_hit_time = current_time
			combo_timer = COMBO_TIME

			# ブロック破壊時にアイテムを生成
			if block.item_type:
				item = block.item_type(block.rect.centerx, block.rect.centery)
				all_sprites.add(item)
				items.add(item)

	# アイテム取得処理
	item_collisions = pygame.sprite.spritecollide(paddle, items, True)
	for item in item_collisions:
		if isinstance(item, PowerUp):
			paddle.rect.width += 25
			if paddle.rect.width > SCREEN_WIDTH / 2:
				paddle.rect.width = SCREEN_WIDTH / 2
			paddle.image = pygame.transform.scale(paddle.original_image, (paddle.rect.width, paddle.rect.height))
			paddle.rect = paddle.image.get_rect(center=paddle.rect.center)
		elif isinstance(item, SpeedDown):
			for ball in balls:
				ball.speed_x *= 0.7
				ball.speed_y *= 0.7
		elif isinstance(item, MultiBall):
			new_ball = Ball(paddle, stage, is_original=False)
			new_ball.rect.center = random.choice(balls.sprites()).rect.center
			new_ball.speed_x = random.uniform(-1, 1) * (BALL_SPEED_X + stage)
			new_ball.speed_y = -random.uniform(0.5, 1) * (BALL_SPEED_Y + stage)
			new_ball.launched = True
			balls.add(new_ball)
			all_sprites.add(new_ball)
		elif isinstance(item, ExtraLife):
			lives += 1

	# ゲームオーバー処理
	if len(balls) == 0:
		lives -= 1
		if lives <= 0:
			game_over = True
			if score > high_score:
				high_score = score
				with open("highscore.txt", "w") as file:
					file.write(str(high_score))
			show_game_over_screen(score)
			stage = 1
			reset_game(stage)
			game_over = False
		else:
			ball = Ball(paddle, stage)
			balls.add(ball)
			all_sprites.add(ball)

	if len(blocks) == 0:
		stage += 1
		show_stage_clear_screen(stage)
		reset_game(stage)

	screen.fill(DARK_BLUE)
	all_sprites.draw(screen)
	balls.draw(screen)

	# 情報表示
	score_text = FONT.render(f"Score: {score}", True, WHITE)
	screen.blit(score_text, (20, 20))		
	lives_text = FONT.render(f"Lives: {lives}", True, WHITE)
	screen.blit(lives_text, (SCREEN_WIDTH - 140, 20))
	high_score_text = FONT.render(f"High Score: {high_score}", True, WHITE)
	screen.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, 20))

	# コンボ表示
	if combo > 1:
		combo_text = FONT.render(f"Combo: x{combo}", True, YELLOW)
		screen.blit(combo_text, (20, 60))

	#windowの更新
	pygame.display.flip()
	clock.tick(60)
