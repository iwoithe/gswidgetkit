# ----------------------------------------------------------------------------
# gswidgetkit Copyright 2021-2022 by Noah Rahm and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------

import wx
from wx.lib.newevent import NewCommandEvent

from .constants import ACCENT_COLOR, NUMBERFIELD_BG_COLOR, TEXT_COLOR
from .textctrl import StyledTextCtrl
from .utils import GetTextExtent

numberfield_cmd_event, EVT_NUMBERFIELD = NewCommandEvent()
numberfield_change_cmd_event, EVT_NUMBERFIELD_CHANGE = NewCommandEvent()


class NumberField(wx.Control):
    """ 
    Number field widget to select an integer. Supports both precise and imprecise
    editing (via dragging the cursor).

    :param wx.Window `parent`: parent window. Must not be ``None``.
    :param integer `id`: window identifier. A value of -1 indicates a default value.
    :param string `label`: the displayed text on the Numberfield label.
    :param integer `default_value`: the default value.
    :param integer `min_value`: the minimum value the control can be set to.
    :param integer `max_value`: the maximum value the control can be set to.
    :param string `suffix`: the label text shown directly after the value.
    :param bool `show_p`: if True, show the progress in the background of the control.
    :param bool `disable_precise`: if True, disable the ability to edit the value via typing in a precise value.
    :param bool `scroll_horz`: if True, the user can scroll horizontally with the mouse.
    """
    def __init__(self, parent, id=wx.ID_ANY, label="", default_value=0, min_value=0,
                 max_value=100, suffix="px", show_p=True, disable_precise=False,
                 scroll_horz=True, size=wx.DefaultSize):
        wx.Control.__init__(self, parent, id, pos=wx.DefaultPosition,
                            size=size, style=wx.NO_BORDER)

        self.parent = parent
        self.focused = False
        self.mouse_in = False
        self.control_size = wx.DefaultSize
        self.show_p = show_p
        self.disable_precise = disable_precise
        self.buffer = None

        if scroll_horz is True:
            self.scroll_dir = 0
        else:
            self.scroll_dir = 1

        self.cur_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.change_rate = .5
        self.change_value = 0
        self.suffix = suffix
        self.value_range = [i for i in range(min_value, max_value)]
        self.label = label

        self.padding_x = 20
        self.padding_y = 10

        # Flag that is true if a drag is happening after a left click
        self.changing_value = False

        # Keep track of last sent event
        self.last_sent_event = None

        # The point in which the cursor gets anchored to during the drag event
        self.anchor_point = (0, 0)

        # Text ctrl
        self.textctrl = StyledTextCtrl(self, value=str(self.cur_value),
                                       bg_color=NUMBERFIELD_BG_COLOR,
                                       style=wx.BORDER_NONE, pos=(0, 0),
                                       size=(10, 24))
        self.textctrl.Hide()
        self.textctrl.Bind(wx.EVT_KILL_FOCUS, self.OnHideTextCtrl)
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown, self)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp, self)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnShowTextCtrl)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, event):
        wx.BufferedPaintDC(self, self.buffer)

    def OnSize(self, event):
        size = self.GetClientSize()

        # Make sure size is at least 1px to avoid
        # strange "invalid bitmap size" errors.
        if size[0] < 1:
            size = (1, 1)
        self.buffer = wx.Bitmap(*size)
        self.UpdateDrawing()

    def UpdateDrawing(self):
        dc = wx.MemoryDC()
        dc.SelectObject(self.buffer)
        dc = wx.GCDC(dc)
        self.OnDrawBackground(dc)
        self.OnDrawWidget(dc)
        del dc  # need to get rid of the MemoryDC before Update() is called.
        self.Refresh()
        self.Update()

    def OnDrawBackground(self, dc):
        dc.SetBackground(wx.Brush(self.parent.GetBackgroundColour()))
        dc.Clear()

    def OnDrawWidget(self, dc):
        fnt = self.parent.GetFont()
        dc.SetFont(fnt)
        dc.SetPen(wx.TRANSPARENT_PEN)

        full_val_lbl = str(self.cur_value)+self.suffix

        width = self.Size[0]
        height = self.Size[1]
        one_val = (width) / (self.max_value + abs(self.min_value))
        self.p_val = round(((self.cur_value + abs(self.min_value))*one_val))

        if self.mouse_in:
            p_color = wx.Colour(ACCENT_COLOR)
            bg_color = wx.Colour(NUMBERFIELD_BG_COLOR)
        else:
            p_color = wx.Colour(ACCENT_COLOR).ChangeLightness(90)
            bg_color = wx.Colour(NUMBERFIELD_BG_COLOR).ChangeLightness(85)
        dc.SetTextForeground(wx.Colour(TEXT_COLOR))
        dc.SetBrush(wx.Brush(bg_color))
        dc.DrawRoundedRectangle(0, 0, width, height, 4)

        if self.show_p is True:
            dc.SetBrush(wx.Brush(p_color))
            dc.DrawRoundedRectangle(0, 0, self.p_val, height, 4)

            if self.p_val < width-4 and self.p_val > (self.min_value+4):
                dc.DrawRectangle((self.p_val)-4, 0, 4, height)

        lbl_w, lbl_h = GetTextExtent(self.label)
        val_w, val_h = GetTextExtent(full_val_lbl)

        dc.DrawText(self.label, self.padding_x, int((height/2) - (lbl_h/2)))
        dc.DrawText(full_val_lbl, (width-self.padding_x) - (val_w), int((height/2) - (val_h/2)))

        # Update position of textctrl
        self.textctrl.SetPosition((5, (int(self.Size[1]/2) - 10)))
        self.textctrl.SetSize((int(self.Size[0]-10), 24))

    def OnKey(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_RETURN:
            self.mouse_in = False
            self.focused = False
            self.OnHideTextCtrl(None)
            self.UpdateDrawing()
        else:
            event.Skip()

    def OnMouseMotion(self, event):
        """
        When the mouse moves, it check to see if it is a drag, or if left down had happened.
        If neither of those cases are true then it will cancel the action.
        If they are true then it calculates the change in position of the mouse, then changes
        the position of the cursor back to where the left click event happened.
        """
        # Changes the cursor
        if self.changing_value:
            self.SetCursor(wx.Cursor(wx.CURSOR_BLANK))
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))

        # Calculate the change in mouse position
        cur_point = event.GetPosition()
        self.delta = cur_point[self.scroll_dir] - self.anchor_point[self.scroll_dir]

        # If the cursor is being moved and dragged left or right
        if self.delta != 0 and event.Dragging() and self.changing_value:
            self.UpdateWidget()
            self.UpdateDrawing()

        if event.Dragging() and self.changing_value:
            self.SetCursor(wx.Cursor(wx.CURSOR_BLANK))
            # Set the cursor back to the original point so it doesn't run away
            if "wxMac" not in wx.PlatformInfo:
                self.WarpPointer(int(self.anchor_point[0]), int(self.anchor_point[1]))

        # Case where the mouse is moving over the control, but has no
        # intent to actually change the value
        if self.changing_value and not event.Dragging():
            self.changing_value = False
            self.parent.SetDoubleBuffered(False)

        event.Skip()

    def OnHideTextCtrl(self, event):
        value = self.textctrl.GetValue()
        if value != " ":
            new_value = int(value)
            if new_value in self.value_range:
                if new_value >= self.min_value and new_value <= self.max_value:
                    self.cur_value = new_value
        self.textctrl.Hide()
        self.SendChangeEvent()
        self.SendSliderEvent()
        self.UpdateDrawing()

    def OnShowTextCtrl(self, event):
        if self.show_p is False and self.disable_precise is False:
            self.textctrl.SetValue(str(self.cur_value))
            self.textctrl.Show()
            self.textctrl.SetFocus()
        event.Skip()
        self.textctrl.SetCurrentPos(len(str(self.cur_value+1)))

    def SendSliderEvent(self):
        wx.PostEvent(self, numberfield_cmd_event(id=self.GetId(), value=self.cur_value))

    def SendChangeEvent(self):
        # Implement a debounce system where only one event is
        # sent only if the value actually changed.
        if self.cur_value != self.last_sent_event:
            wx.PostEvent(self, numberfield_change_cmd_event(
                                    id=self.GetId(), value=self.cur_value))
            self.last_sent_event = self.cur_value

    def Increasing(self):
        if self.delta > 0:
            return True
        else:
            return False

    def Decreasing(self):
        if self.delta < 0:
            return True
        else:
            return False

    def OnLeftUp(self, event):
        """
        Cancels the changing event, and turns off the optimization buffering
        """
        self.changing_value = False
        self.parent.SetDoubleBuffered(False)
        self.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
        self.SendSliderEvent()

    def OnLeftDown(self, event):
        """
        Sets the anchor point that the cursor will go back to the original position.
        Also turns on the doublebuffering which eliminates the flickering when rapidly changing values.
        """
        pos = event.GetPosition()
        self.anchor_point = (pos[0], pos[1])
        self.changing_value = True
        self.parent.SetDoubleBuffered(True)
        self.UpdateDrawing()

    def OnSetFocus(self, event):
        self.focused = True
        self.Refresh()

    def OnKillFocus(self, event):
        self.focused = False
        self.Refresh()

    def OnMouseEnter(self, event):
        self.mouse_in = True
        self.Refresh()
        self.UpdateDrawing()

    def OnMouseLeave(self, event):
        """
        In the event that the mouse is moved fast enough to leave the bounds of the label, this
        will be triggered, warping the cursor back to where the left click event originally
        happened
        """
        if self.changing_value:
            self.WarpPointer(self.anchor_point[0], self.anchor_point[1])
        self.mouse_in = False
        self.Refresh()
        self.UpdateDrawing()

    def AcceptsFocusFromKeyboard(self):
        """Overridden base class virtual."""
        return True

    def AcceptsFocus(self):
        """ Overridden base class virtual. """
        return True

    def HasFocus(self):
        """ Returns whether or not we have the focus. """
        return self.focused

    def GetValue(self):
        return self.cur_value

    def SetValue(self, value):
        self.cur_value = value

    def SetLabel(self, label):
        self.label = label

    def UpdateWidget(self):
        self.change_value += self.change_rate/2.0

        if self.change_value >= 1:
            if self.Increasing():
                if self.cur_value < self.max_value:
                    self.cur_value += 1
            else:
                if (self.cur_value - 1) >= self.min_value:
                    if self.cur_value > self.min_value:
                        self.cur_value -= 1

            # Reset the change value since the value was just changed.
            self.change_value = 0

        self.SendChangeEvent()

    def DoGetBestSize(self):
        """
        Overridden base class virtual.  Determines the best size of the control
        based on the label size, the bitmap size and the current font.
        """

        normal_label = self.label
        value_label = str(self.cur_value) + self.suffix

        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)

        dc = wx.ClientDC(self)
        dc.SetFont(font)

        # Measure our labels
        lbl_text_w, lbl_text_h = dc.GetTextExtent(normal_label)
        val_text_w, val_text_h = dc.GetTextExtent(value_label)

        totalwidth = lbl_text_w + val_text_w + self.padding_x + 76

        # To avoid issues with drawing the control properly, we
        # always make sure the width is an even number.
        if totalwidth % 2:
            totalwidth -= 1
        totalheight = lbl_text_h + self.padding_y

        best = wx.Size(totalwidth, totalheight)

        # Cache the best size so it doesn't need to be calculated again,
        # at least until some properties of the window change
        self.CacheBestSize(best)

        return best
