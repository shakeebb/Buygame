# import thorpy, pygame
#
# class HelpMenu:
#     def __init__(self, x, y):
#         self.x = x
#         self.y = y
#         self.box = None
#         self.menu = None
#     pygame.init()
#     thorpy.set_theme("human")
#     e_title = thorpy.make_text("Help", font_size=20, font_color=(0,0,150))
#     e_title.center() #center the title on the screen
#     e_title.set_topleft((None, 10)) #set the y-coord at 10
#     e_play = thorpy.make_button("Play!", func=None) #launch the game
#     varset = thorpy.VarSet() #here we will declare options that user can set
#     varset.add("trials", value=5, text="Trials:", limits=(1, 20))
#     varset.add("player name", value="Name Here", text="Player name:")
#     e_options = thorpy.ParamSetterLauncher.make([varset], "Options", "Options")
#     e_quit = thorpy.make_button("Quit", func=thorpy.functions.quit_menu_func)
#     box = thorpy.Box(elements=[e_title, e_play, e_options, e_quit])
#     menu = thorpy.Menu(box)
#     self.box = box
#     self.menu = menu
