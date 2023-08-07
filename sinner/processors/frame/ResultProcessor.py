import os
from typing import Callable

from sinner.Status import Mood
from sinner.typing import Frame
from sinner.validators.AttributeLoader import Rules
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.utilities import is_absolute_path


class ResultProcessor(BaseFrameProcessor):
    source_path: str

    def rules(self) -> Rules:
        return super().rules() + [
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path',
            },
            {
                'parameter': {'output', 'output-path'},
                'attribute': 'output_path',
                'default': lambda: self.suggest_output_path(),
                'valid': lambda: is_absolute_path(self.output_path),
                'help': 'Select an output file or a directory'
            }
        ]

    def suggest_output_path(self) -> str:
        target_name, target_extension = os.path.splitext(os.path.basename(self.target_path))
        prefix = 'result-' if self.source_path is None else os.path.splitext(os.path.basename(self.source_path))[0]+'-'
        if self.output_path is None:
            return os.path.join(os.path.dirname(self.target_path), prefix + target_name + target_extension)
        if os.path.isdir(self.output_path):
            return os.path.join(self.output_path, prefix + target_name + target_extension)
        return self.output_path

    def process(self, desc: str = 'Processing', set_progress: Callable[[int], None] | None = None) -> None:
        self.handler = self.suggest_handler(self.target_path, self.parameters)
        if self.state.target_path is not None:
            self.handler.result(from_dir=self.state.target_path, filename=self.output_path, audio_target=self.target_path)
        else:
            self.update_status('Target path is empty, ignoring', mood=Mood.BAD)

    def process_frame(self, frame: Frame) -> Frame:
        return frame
