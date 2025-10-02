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
#   10. Extract current page*
#   20. Extract pages*
#   30. Save*
#   40. Save as
#   50. Close*
#   100. Exit
class FileMenuItems:
    OPEN = lambda app, window: toga.Command(
        window.open_dialog,
        text = _('Open'),
        icon = app.paths.app / 'resources/icons/open.png',
        shortcut = toga.Key.MOD_1 + 'O',
        tooltip = _('Open a PDF file'),
        order = 0,
        enabled = True,
        group = RootMenus.FILE,
    )
    EXTRACT_PAGE = lambda app, window: toga.Command(
        window.extract_current_page,
        text = _('Extract current page'),
        #icon,
        tooltip = _('Extract current page'),
        order = 10,
        group = RootMenus.FILE,
        enabled = False,
        id = 'extract_current_page'
    )
    EXTRACT_PAGES = lambda app, window: toga.Command(
        window.open_extract_pages_window,
        text = _('Extract pages'),
        #icon
        tooltip = _('Extract one or more pages from current document'),
        order = 20,
        group = RootMenus.FILE,
        enabled = False,
        id = 'extract_pages',
    )
    SAVE = lambda app, window: toga.Command(
        window.save_tab,
        text = _('Save'),
        shortcut = toga.Key.MOD_1 + 'S',
        #icon,
        tooltip = _('Save file'),
        order = 30,
        group = RootMenus.FILE,
        enabled = False,
        id = 'save_file',
    )
    CLOSE = lambda app, window: toga.Command(
        window.close_tab,
        text = _('Close'),
        shortcut = toga.Key.MOD_1 + 'W',
        #icon,
        tooltip = _('Close current tab'),
        order = 50,
        group = RootMenus.FILE,
        enabled = False,
        id = 'close_tab',
    )
    EXIT = lambda app, window: toga.Command(
        app.request_exit,
        text = _('Exit'),
        shortcut = toga.Key.MOD_1 + 'Q',
        tooltip = _('Exit app'),
        order = 100,
        group = RootMenus.FILE,
        enabled = True,
    )

    def create_commands(app, window, menu, toolbar):
        for item in [
            FileMenuItems.OPEN,
            FileMenuItems.EXTRACT_PAGE,
            FileMenuItems.EXTRACT_PAGES,
            FileMenuItems.SAVE,
            FileMenuItems.CLOSE,
        ]:
            toolbar.add(item(app, window))
        for item in [FileMenuItems.EXIT]:
            menu.add(item(app, window))

class CreateMenuItems:
    MERGE = lambda app, window: toga.Command(
        window.open_merge_window,
        text = _('Merge'),
        shortcut = toga.Key.MOD_1 + 'M',
        icon = app.paths.app / 'resources/icons/merge.png',
        tooltip = _('Merge two or more PDF documents'),
        order = 0,
        group = RootMenus.CREATE,
        enabled = True,
    )

    def create_commands(app, window, menu, toolbar):
        for item in [CreateMenuItems.MERGE]:
            toolbar.add(item(app, window))
        for item in []:
            menu.add(item(app, window))

def create_commands(app, window, menu, toolbar):
    FileMenuItems.create_commands(app, window, menu, toolbar)
    CreateMenuItems.create_commands(app, window, menu, toolbar)
