import inspect
import os.path
from abc import ABC, abstractmethod
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any

from tqdm import tqdm

from roop.handlers.frames.BaseFramesHandler import BaseFramesHandler
from roop.parameters import Parameters
from roop.state import State
from roop.typing import Frame
from roop.utilities import update_status, load_class, get_mem_usage


class BaseFrameProcessor(ABC):
    state: State
    execution_providers: List[str]
    execution_threads: int
    max_memory: int
    statistics: dict[str, int] = {'mem_rss_max': 0, 'mem_vms_max': 0}

    @staticmethod
    def create(processor_name: str, parameters: Parameters, state: State) -> 'BaseFrameProcessor':  # processors factory
        handler_class = load_class(os.path.dirname(__file__), processor_name)

        if handler_class and issubclass(handler_class, BaseFrameProcessor):
            class_parameters_list = inspect.signature(handler_class.__init__).parameters
            params: dict[str, Any] = {}
            for parameter_name in class_parameters_list.keys():
                if hasattr(parameters, parameter_name):
                    params[parameter_name] = getattr(parameters, parameter_name)
            params['state'] = state
            return handler_class(**params)
        else:
            raise ValueError(f"Invalid processor name: {processor_name}")

    def __init__(self, execution_providers: List[str], execution_threads: int, max_memory: int, state: State) -> None:
        self.execution_providers = execution_providers
        self.execution_threads = execution_threads
        self.max_memory = max_memory
        self.state = state
        if not self.validate():
            quit()

    def statistics_get(self, param: str) -> int:
        return self.statistics[param]

    def statistics_set(self, param: str, value: int) -> None:
        self.statistics[param] = value

    def get_mem_usage(self) -> str:
        mem_rss = get_mem_usage()
        mem_vms = get_mem_usage('vms')
        if self.statistics_get('mem_rss_max') < mem_rss:
            self.statistics_set('mem_rss_max', mem_rss)
        if self.statistics_get('mem_vms_max') < mem_vms:
            self.statistics_set('mem_vms_max', mem_vms)
        return '{:.2f}'.format(mem_rss).zfill(5) + 'MB [MAX:{:.2f}'.format(self.statistics_get('mem_rss_max')).zfill(5) + 'MB]' + '/' + '{:.2f}'.format(mem_vms).zfill(5) + 'MB [MAX:{:.2f}'.format(
            self.statistics_get('mem_vms_max')).zfill(5) + 'MB]'

    def process(self, frames_handler: BaseFramesHandler, desc: str = 'Processing') -> None:
        self.state.processor_name = self.__class__.__name__
        frames_handler.current_frame_index = self.state.extracted_frames_count() + 1
        frames_path_list = frames_handler.get_frames_paths(self.state.in_dir)
        if self.state.is_started():
            update_status(f'Temp resources for this target already exists with {self.state.processed_frames_count()} frames processed, continue processing...')
        with tqdm(
                total=self.state.frames_count,
                desc=desc, unit='frame',
                dynamic_ncols=True,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
                initial=self.state.processed_frames_count() + 1
        ) as progress:
            self.multi_process_frame(frames_path_list=frames_path_list, process_frames=self.process_frames, progress=progress)

    @abstractmethod
    def process_frame(self, temp_frame_path: str) -> Frame:
        pass

    def process_frames(self, frame: tuple[int, str]) -> None:  # type: ignore[type-arg]
        try:
            self.state.save_temp_frame(self.process_frame(frame[1]), frame[0])
        except Exception as exception:
            print(exception)
            pass

    def multi_process_frame(self, frames_path_list: List[tuple[int, str]], process_frames: Callable[[tuple[int, str]], None], progress: None | tqdm = None) -> None:  # type: ignore[type-arg]
        def future_remove(future_: Future):
            futures.remove(future_)
            progress.update()
            progress.set_postfix({
                'memory_usage': self.get_mem_usage(),
                'futures': len(futures)
            })

        with ThreadPoolExecutor(max_workers=self.execution_threads) as executor:
            futures = []
            for frame in frames_path_list:
                future: Future = executor.submit(process_frames, frame)
                future.add_done_callback(future_remove)
                futures.append(future)
                progress.set_postfix({
                    'memory_usage': self.get_mem_usage(),
                    'futures': len(futures)
                })
                if get_mem_usage('vms', 'g') >= self.max_memory:
                    futures[:1][0].result()
            for future in as_completed(futures):
                future.result()

    @staticmethod
    def validate() -> bool:
        return True
