import glob
import os.path
from typing import List

import cv2
from cv2 import VideoCapture

from roop.handlers.frames.BaseFramesHandler import BaseFramesHandler
from roop.typing import Frame
from roop.utilities import write_image


class CV2VideoHandler(BaseFramesHandler):

    def open(self) -> VideoCapture:
        cap = cv2.VideoCapture(self._target_path)
        if not cap.isOpened():
            raise Exception("Error opening frames file")
        return cap

    def detect_fps(self) -> float:
        capture = self.open()
        fps = capture.get(cv2.CAP_PROP_FPS)
        capture.release()
        return fps

    def detect_fc(self) -> int:
        capture = self.open()
        video_frame_total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        capture.release()
        return video_frame_total

    def get_frames_paths(self, to_dir: str) -> List[str]:
        capture = self.open()
        i = 1
        while True:
            ret, frame = capture.read()
            if not ret:
                break
            write_image(frame, os.path.join(to_dir, f"{i:04d}.png"))
            i += 1
        capture.release()
        return super().get_frames_paths(to_dir)

    def extract_frame(self, frame_number: int) -> tuple[Frame, int]:
        capture = self.open()
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = capture.read()
        capture.release()
        if not ret:
            raise Exception(f"Error reading frame {frame_number}")
        return frame, frame_number

    def result(self, from_dir: str, filename: str, fps: None | float, audio_target: str | None = None) -> bool:
        if fps is None:
            fps = self.fps
        if audio_target is not None:
            print('Sound is not supported in CV2VideoHandler')
        try:
            frame_files = glob.glob(os.path.join(glob.escape(from_dir), '*.png'))
            first_frame = cv2.imread(frame_files[0])
            height, width, channels = first_frame.shape
            fourcc = cv2.VideoWriter_fourcc(*'H264')  # Specify the frames codec
            video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
            for frame_path in frame_files:
                frame = cv2.imread(frame_path)
                video_writer.write(frame)
            video_writer.release()
            return True
        except Exception:
            return False