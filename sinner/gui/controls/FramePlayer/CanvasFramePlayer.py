from tkinter import Canvas, BOTH, TOP

import cv2
from PIL import Image
from PIL.ImageTk import PhotoImage

from sinner.gui.controls.FramePlayer.BaseFramePlayer import BaseFramePlayer
from sinner.helpers.FrameHelper import resize_proportionally
from sinner.typing import Frame


# Note: because this player based on a tkinter.canvas, it should be packed and configured after initialization
class CanvasFramePlayer(Canvas, BaseFramePlayer):
    photo: PhotoImage | None = None

    def __init__(self, master=None, cnf=None, **kw):
        if cnf is None:
            cnf = {}
        Canvas.__init__(self, master=master, cnf=cnf, **kw)
        BaseFramePlayer.__init__(self)

    @property
    def photo_image(self) -> PhotoImage | None:
        return self.photo

    @photo_image.setter
    def photo_image(self, image: PhotoImage | None) -> None:
        try:  # todo add display modes, add handler on empty image
            self.create_image(self.winfo_width() // 2, self.winfo_height() // 2, image=image)
            self.photo = image
        except Exception as e:
            pass

    def show_frame(self, frame: Frame | None = None, resize: bool | tuple[int, int] | None = True) -> None:
        if frame is None and self._last_frame is not None:
            frame = self._last_frame
        if frame is not None:
            self._last_frame = frame
            if resize is True:  # resize to the current canvas size
                frame = resize_proportionally(frame, (self.winfo_height(), self.winfo_width()))
            elif isinstance(resize, tuple):
                frame = resize_proportionally(frame, resize)
            elif resize is False:  # resize the canvas to the image size
                self.adjust_size()
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.photo_image = PhotoImage(image)

    def save_to_file(self, filename: str) -> None:
        if self._last_frame is not None:
            Image.fromarray(cv2.cvtColor(self._last_frame, cv2.COLOR_BGR2RGB)).save(filename)

    def adjust_size(self) -> None:
        if self._last_frame is not None:
            self.configure(width=self._last_frame.shape[1], height=self._last_frame.shape[0])
