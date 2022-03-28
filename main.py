import pygame
from mine import Field, Win

done = False
screen = pygame.display.set_mode((800, 600))
win = Win()
field = Field(win, (10, 10), (10, 10))

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)
        field.check_event(event)
        win.check_event(event)
    screen.fill((53, 58, 74))
    win.render(screen)
    pygame.display.update()
