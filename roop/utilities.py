import mimetypes
import os
import platform
import shutil
import urllib
from pathlib import Path
from typing import List

import cv2
import tensorflow
from numpy import array, uint8, fromfile
from tqdm import tqdm

from roop.handlers.video.BaseVideoHandler import BaseVideoHandler
from roop.handlers.video.CV2VideoHandler import CV2VideoHandler
from roop.handlers.video.FFmpegVideoHandler import FFmpegVideoHandler
from roop.parameters import Parameters
from roop.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from roop.processors.frame.FaceSwapper import FaceSwapper
from roop.state import State
from roop.typing import Frame

TEMP_FILE = 'temp.mp4'
TEMP_DIRECTORY = 'temp'


def limit_resources(max_memory: int) -> None:
    # prevent tensorflow memory leak
    gpus = tensorflow.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tensorflow.config.experimental.set_memory_growth(gpu, True)
    # limit memory usage
    if max_memory:
        memory = max_memory * 1024 ** 3
        if platform.system().lower() == 'darwin':
            memory = max_memory * 1024 ** 6
        if platform.system().lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def get_video_handler(target_path: str, handler_name: str = 'ffmpeg') -> BaseVideoHandler:  # temporary, will be replaced with a factory
    if 'cv2' == handler_name:
        return CV2VideoHandler(target_path)
    return FFmpegVideoHandler(target_path)


def get_frame_processor(params: Parameters, state_var: State) -> BaseFrameProcessor:  # temporary, will be replaced with a factory
    return FaceSwapper(params, state_var)


def update_status(message: str, caller: str = 'GLOBAL') -> None:
    print(f'[{caller}] {message}')
    # if not roop.globals.headless:
    #      ui.update_status(message)


def get_temp_directory_path(target_path: str) -> str:
    target_name, _ = os.path.splitext(os.path.basename(target_path))
    target_directory_path = os.path.dirname(target_path)
    return os.path.join(target_directory_path, TEMP_DIRECTORY, target_name)


def get_temp_output_path(target_path: str) -> str:
    temp_directory_path = get_temp_directory_path(target_path)
    return os.path.join(temp_directory_path, TEMP_FILE)


def normalize_output_path(source_path: str, target_path: str, output_path: str) -> str:
    if source_path and target_path:
        source_name, _ = os.path.splitext(os.path.basename(source_path))
        target_name, target_extension = os.path.splitext(os.path.basename(target_path))
        if os.path.isdir(output_path):
            return os.path.join(output_path, source_name + '-' + target_name + target_extension)
    return output_path


def create_temp(target_path: str) -> str:
    temp_directory_path = get_temp_directory_path(target_path)
    Path(temp_directory_path).mkdir(parents=True, exist_ok=True)
    return temp_directory_path


def move_temp(target_path: str, output_path: str) -> None:
    temp_output_path = get_temp_output_path(target_path)
    if os.path.isfile(temp_output_path):
        if os.path.isfile(output_path):
            os.remove(output_path)
        shutil.move(temp_output_path, output_path)


def clean_temp(target_path: str, keep_frames: bool = False) -> None:
    temp_directory_path = get_temp_directory_path(target_path)
    parent_directory_path = os.path.dirname(temp_directory_path)
    if not keep_frames and os.path.isdir(temp_directory_path):
        shutil.rmtree(temp_directory_path)
    if os.path.exists(parent_directory_path) and not os.listdir(parent_directory_path):
        os.rmdir(parent_directory_path)


def has_image_extension(image_path: str) -> bool:
    return image_path.lower().endswith(('png', 'jpg', 'jpeg'))


def is_image(image_path: str | None) -> bool:
    if image_path is not None and image_path and os.path.isfile(image_path):
        mimetype, _ = mimetypes.guess_type(image_path)
        return bool(mimetype and mimetype.startswith('image/'))
    return False


def is_video(video_path: str) -> bool:
    if video_path and os.path.isfile(video_path):
        mimetype, _ = mimetypes.guess_type(video_path)
        return bool(mimetype and mimetype.startswith('video/'))
    return False


def conditional_download(download_directory_path: str, urls: List[str]) -> None:
    if not os.path.exists(download_directory_path):
        os.makedirs(download_directory_path)
    for url in urls:
        download_file_path = os.path.join(download_directory_path, os.path.basename(url))
        if not os.path.exists(download_file_path):
            request = urllib.request.urlopen(url)  # type: ignore[attr-defined]
            total = int(request.headers.get('Content-Length', 0))
            with tqdm(total=total, desc='Downloading', unit='B', unit_scale=True, unit_divisor=1024) as progress:
                urllib.request.urlretrieve(url, download_file_path, reporthook=lambda count, block_size, total_size: progress.update(block_size))  # type: ignore[attr-defined]


def resolve_relative_path(path: str) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))


def read_image(path: str) -> Frame:
    if platform.system().lower() == 'windows':  # issue #511
        return cv2.imdecode(fromfile(path, dtype=uint8), cv2.IMREAD_UNCHANGED)
    else:
        return cv2.imread(path)


def write_image(image: Frame, path: str) -> bool:
    if platform.system().lower() == 'windows':  # issue #511
        is_success, im_buf_arr = cv2.imencode(".png", image)
        im_buf_arr.tofile(path)
        return is_success
    else:
        return cv2.imwrite(path, array)
