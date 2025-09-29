from toga.style import pack
from toga import constants

MARGIN = 5
THUMBNAIL = 100

row_margin = pack.Pack(direction=constants.ROW, margin=MARGIN)
row_margin_center = pack.Pack(direction=constants.ROW, margin=MARGIN, vertical_align_items=constants.CENTER)
flex_margin = pack.Pack(flex=1, margin=MARGIN)
flex_column_right = pack.Pack(flex=1, direction=constants.COLUMN, align_items=constants.END)
flex_column_center_margin = pack.Pack(flex=1, direction=constants.COLUMN, align_items=constants.CENTER, margin=MARGIN)
flex_row_right = pack.Pack(flex=1, direction=constants.ROW, align_items=constants.END)
margin = pack.Pack(margin=MARGIN)
right_align = pack.Pack(flex=0, direction=constants.ROW, align_items=constants.END)
thumbnail_margin = pack.Pack(margin=MARGIN, height=100)