import os
import threading
from typing import Any, List, Callable

import insightface
from tqdm import tqdm

from roop.face_analyser import FaceAnalyser
from roop.parameters import Parameters
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.state import State
from roop.typing import Face, Frame
from roop.utilities import is_image, read_image, is_video, resolve_relative_path, conditional_download, write_image, create_temp, update_status


# процессор ничего не знает о видео, у него на входе набор кадров, на выходе набор кадров

class FaceSwapper(BaseFrameProcessor):
    source: [None, str] = None  # none | file path
    target: [None, str] = None  # none | file path
    many_faces: bool = False
    state: State

    _face_analyser: FaceAnalyser
    _face_swapper: Any  # todo type
    _source_face: [None, Face]  # todo type

    THREAD_LOCK = threading.Lock()

    def __init__(self, params: Parameters, state: State):
        download_directory_path = resolve_relative_path('../models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/inswapper_128.onnx'])
        self._face_analyser = FaceAnalyser(self.execution_providers)
        super().__init__(params)
        self.many_faces = params.many_faces
        self.state = state
        self._face_swapper = insightface.model_zoo.get_model(resolve_relative_path('../models/inswapper_128.onnx'), providers=self.execution_providers)

    def validate(self):
        if not is_image(self.source):
            update_status('Select an image for source path.')
            return False
        self._source_face = self._face_analyser.get_one_face(read_image(self.source))
        if not self._source_face:
            update_status('No face in source path detected.')
            return False
        return True

    def swap_face(self, target_face: Face, temp_frame: Frame) -> Frame:
        return self._face_swapper.get(temp_frame, target_face, self._source_face, paste_back=True)

    def process_frame(self, temp_frame: Frame) -> Frame:
        if self.many_faces:
            many_faces = self._face_analyser.get_many_faces(temp_frame)
            if many_faces:
                for target_face in many_faces:
                    temp_frame = self.swap_face(target_face, temp_frame)
        else:
            target_face = self._face_analyser.get_one_face(temp_frame)
            if target_face:
                temp_frame = self.swap_face(target_face, temp_frame)
        return temp_frame

    def process_frames(self, tmp: Any, temp_frame_paths: List[str], progress: [None, tqdm] = None) -> None:
        for temp_frame_path in temp_frame_paths:
            temp_frame = read_image(temp_frame_path)
            try:
                result = self.process_frame(temp_frame)
                processed_frame_path = self.state.get_frame_processed_name(temp_frame_path)
                write_image(result, processed_frame_path)
                os.remove(temp_frame_path)
            except Exception as exception:
                print(exception)
                pass
            if progress:
                progress.update(1)

    def process(self):
        update_status(f'Temp resources for this target already exists with {self.state.processed_frames_count()} frames processed, continue processing...')
        progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
        total = self.state.total_frames_count()
        with tqdm(total=total, desc='Processing', unit='frame', dynamic_ncols=True, bar_format=progress_bar_format, initial=self.state.processed_frames_count()) as progress:
            progress.set_postfix({'execution_providers': self.execution_providers, 'threads': self.execution_threads, 'memory': self.max_memory})
            self.multi_process_frame(self.source, self.state.unprocessed_frames(), self.process_frames, progress)