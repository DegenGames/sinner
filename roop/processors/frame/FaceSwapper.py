import threading
from typing import List

import insightface

from roop.face_analyser import FaceAnalyser
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.state import State
from roop.typing import Face, Frame, FaceSwapperType
from roop.utilities import resolve_relative_path, conditional_download


class FaceSwapper(BaseFrameProcessor):
    many_faces: bool = False
    source_face: Face

    _face_analyser: FaceAnalyser
    _face_swapper: FaceSwapperType

    thread_lock = threading.Lock()

    def __init__(self, execution_providers: List[str], execution_threads: int, max_memory: int, many_faces: bool, source_face: Frame, state: State):
        download_directory_path = resolve_relative_path('../models')
        conditional_download(download_directory_path, ['https://huggingface.co/henryruhs/roop/resolve/main/inswapper_128.onnx'])
        self._face_analyser = FaceAnalyser(self.execution_providers)
        super().__init__(execution_providers=execution_providers, execution_threads=execution_threads, max_memory=max_memory, state=state)
        self.many_faces = many_faces
        self.source_face = self._face_analyser.get_one_face(source_face)
        self._face_swapper = insightface.model_zoo.get_model(resolve_relative_path('../models/inswapper_128.onnx'), providers=self.execution_providers)

    def swap_face(self, target_face: Face, temp_frame: Frame) -> Frame:
        return self._face_swapper.get(temp_frame, target_face, self.source_face, paste_back=True)

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
