"""Creates menus and toolbar groups
"""
import toga

# Menus (* signals items on toolbar)
#   0. File menu
#  10. Edit menu
#  20. Create menu
# 100. Help menu
class RootMenus:
    FILE = toga.Group(
        text =_('File'),
        id = 'file_menu',
        order = 0,
    )
    EDIT = toga.Group(
        text = _('Edit'),
        id = 'edit_menu',
        order = 10,
    )
    CREATE = toga.Group(
        text = _('Create'),
        id = 'create_menu',
        order = 20,
    )
    HELP = toga.Group(
        text = _('Help'),
        id = 'help_menu',
        order = 100,
    )

class FileSubmenus:
    RECENT_FILES = toga.Group(
        text = _('Open recent'),
        id = 'recent_files_submenu',
        parent = RootMenus.FILE,
        section = 1,
    )

# File menu items:
#   0. Open*
#   10. Close*
#   100. Exit
class FileMenuItems:
    OPEN = lambda app: toga.Command(
        app.open_dialog,
        text = _('Open'),
        icon = app.paths.app / 'resources/icons/open.png',
        shortcut = toga.Key.MOD_1 + 'O',
        tooltip = _('Open a PDF file'),
        order = 0,
        group = RootMenus.FILE,
    )
    CLOSE = lambda app: toga.Command(
        app.close_tab,
        text = _('Close'),
        shortcut = toga.Key.MOD_1 + 'W',
        #icon,
        tooltip = _('Close current tab'),
        order = 10,
        group = RootMenus.FILE,
        enabled = False,
        id = 'close_tab',
    )
    EXIT = lambda app: toga.Command(
        app.request_exit,
        text = _('Exit'),
        shortcut = toga.Key.MOD_1 + 'Q',
        tooltip = _('Exit app'),
        order = 100,
        group = RootMenus.FILE,
        enabled = True,
    )

    def create_commands(app, menu, toolbar):
        for item in [FileMenuItems.OPEN, FileMenuItems.CLOSE]:
            toolbar.add(item(app))
        for item in [FileMenuItems.EXIT]:
            menu.add(item(app))

class CreateMenuItems:
    MERGE = lambda app: toga.Command(
        app.open_merge_window,
        text = _('Merge'),
        shortcut = toga.Key.MOD_1 + 'M',
        icon = app.paths.app / 'resources/icons/merge.png',
        tooltip = _('Merge two or more PDF documents'),
        order = 0,
        group = RootMenus.CREATE
    )

    def create_commands(app, menu, toolbar):
        for item in [CreateMenuItems.MERGE]:
            toolbar.add(item(app))
        for item in []:
            menu.add(item(app))

    def create_menu(app, commandset):
        commandset.add(CreateMenuItems.MERGE(app))
    
    def create_toolbar(app, commandset):
        commandset.add(CreateMenuItems.MERGE(app))

def create_menus(app, commandset):
    FileMenuItems.create_menu(app, commandset)
    CreateMenuItems.create_menu(app, commandset)

def create_toolbar(app, commandset):
    FileMenuItems.create_toolbar(app, commandset)
    CreateMenuItems.create_toolbar(app, commandset)

def create_commands(app, menu, toolbar):
    FileMenuItems.create_commands(app, menu, toolbar)
    CreateMenuItems.create_commands(app, menu, toolbar)
