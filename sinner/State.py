import os
from argparse import Namespace
from pathlib import Path

from sinner.Status import Status
from sinner.typing import Frame
from sinner.utilities import write_image
from sinner.validators.AttributeLoader import AttributeLoader, Rules

OUT_DIR = 'OUT'
IN_DIR = 'IN'


class State(AttributeLoader, Status):
    source_path: str
    target_path: str

    frames_count: int
    processor_name: str
    _temp_dir: str
    _zfill_length: int | None
    _in_dir: str | None = None
    _out_dir: str | None = None

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path'
            }
        ]

    def __init__(self, parameters: Namespace, target_path: str, temp_dir: str, frames_count: int, processor_name: str):
        super().__init__(parameters)
        self.target_path = target_path
        self._temp_dir = temp_dir
        self.frames_count = frames_count
        self.processor_name = processor_name
        self._zfill_length = None
        state = [
            {"Source": getattr(self, "source_path", "None")},
            {"Target": self.target_path},
            {"Temporary dir": self._temp_dir}
        ]
        state_string = "\n".join([f"\t{key}: {value}" for d in state for key, value in d.items()])
        self.update_status(f'The processing state:\n{state_string}')

    @property
    def out_dir(self) -> str:
        if self._out_dir is None:
            self._out_dir = self.make_path(self.state_path(OUT_DIR))
            self.update_status(f'The output directory is {self._out_dir}')
        return self._out_dir

    @out_dir.setter
    def out_dir(self, value: str) -> None:
        self._out_dir = value
        self.update_status(f'The output directory is changed to {self._out_dir}')

    @property
    def in_dir(self) -> str:
        if self._in_dir is None:
            self._in_dir = self.make_path(self.state_path(IN_DIR))
            self.update_status(f'The input directory is {self._in_dir}')
        return self._in_dir

    @in_dir.setter
    def in_dir(self, value: str) -> None:
        self._in_dir = value
        self.update_status(f'The input directory is changed to {self._in_dir}')

    @staticmethod
    def make_path(path: str) -> str:
        if not os.path.exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)
        return path

    def state_path(self, dir_type: str) -> str:
        """
        Processors may not need the source or (in theory) the target. Method tries to configure a part of state path
        for any situation
        :return: adapted state path
        """
        sub_path = (self.processor_name, os.path.basename(self.target_path or ''), os.path.basename(self.source_path or ''), dir_type)
        return os.path.join(self._temp_dir, *sub_path)

    def save_temp_frame(self, frame: Frame, index: int) -> None:
        if not write_image(frame, self.get_frame_processed_name(index)):
            raise Exception(f"Error saving frame: {self.get_frame_processed_name(index)}")

    #  Checks if some frame already processed
    @property
    def is_started(self) -> bool:
        return self.frames_count > self.processed_frames_count > 0

    #  Checks if the process is finished
    @property
    def is_finished(self) -> bool:
        return self.frames_count <= self.processed_frames_count

    #  Returns count of already processed frame for this target (0, if none).
    @property
    def processed_frames_count(self) -> int:
        return len([os.path.join(self.out_dir, file) for file in os.listdir(self.out_dir) if file.endswith(".png")])

    #  Returns count of already extracted frame for this target (0, if none).
    @property
    def extracted_frames_count(self) -> int:
        return len([os.path.join(self.in_dir, file) for file in os.listdir(self.in_dir) if file.endswith(".png")])

    #  Returns count of still unprocessed frame for this target (0, if none).
    @property
    def unprocessed_frames_count(self) -> int:
        return self.frames_count - self.processed_frames_count

    #  Returns a processed file name for an unprocessed frame index
    def get_frame_processed_name(self, frame_index: int) -> str:
        filename = str(frame_index).zfill(self.get_zfill_length) + '.png'
        return str(os.path.join(self.out_dir, filename))

    @property
    def get_zfill_length(self) -> int:
        if self._zfill_length is None:
            self._zfill_length = len(str(self.frames_count))
        return self._zfill_length
