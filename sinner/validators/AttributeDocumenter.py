from typing import Type, List, Dict

from colorama import Style, Fore

from sinner.Benchmark import Benchmark
from sinner.Core import Core
from sinner.Preview import Preview
from sinner.Sinner import Sinner
from sinner.State import State
from sinner.Status import Status
from sinner.handlers.frame.CV2VideoHandler import CV2VideoHandler
from sinner.handlers.frame.DirectoryHandler import DirectoryHandler
from sinner.handlers.frame.FFmpegVideoHandler import FFmpegVideoHandler
from sinner.handlers.frame.ImageHandler import ImageHandler
from sinner.handlers.frame.VideoHandler import VideoHandler
from sinner.processors.frame.FaceEnhancer import FaceEnhancer
from sinner.processors.frame.FaceSwapper import FaceSwapper
from sinner.processors.frame.FrameExtractor import FrameExtractor
from sinner.processors.frame.FrameResizer import FrameResizer
from sinner.processors.frame.ResultProcessor import ResultProcessor
from sinner.validators import AttributeLoader
from sinner.validators.AttributeLoader import VALIDATORS, Rule
from sinner.validators.ValueValidator import ValueValidator

DocumentedClasses: List[Type[AttributeLoader]] = [
    Sinner,
    Core,
    Status,
    State,
    Preview,
    Benchmark,
    FaceEnhancer,
    FaceSwapper,
    FrameExtractor,
    FrameResizer,
    ResultProcessor,
    CV2VideoHandler,
    DirectoryHandler,
    FFmpegVideoHandler,
    ImageHandler,
    VideoHandler
]


class AttributeDocumenter:

    def show_help(self):
        raw_help_doc = self.collect()
        help_doc = self.format(raw_help_doc)
        print(help_doc)
        quit()

    def collect(self) -> List[Dict[str, List[Dict[str, List[str]]]]]:
        collected_doc: List[Dict[str, List[Dict[str, List[str]]]]] = []
        for doc_class in DocumentedClasses:
            class_doc: List[Dict[str, List[str]]] = []
            loaded_class: Type[AttributeLoader] = doc_class.__new__(doc_class)
            loadable_attributes = loaded_class.validating_attributes()
            for attribute in loadable_attributes:
                parameters: List[str] = loaded_class.get_attribute_parameters(attribute)
                help_string: str | None = loaded_class.get_attribute_help(attribute)
                defaults = None
                rules = loaded_class.get_attribute_rules(attribute)
                if 'default' in rules:
                    defaults = self.format_default(rules['default'])
                choices = self.format_choices(rules)
                class_doc.append({'parameter': parameters, 'help': help_string, 'defaults': defaults, 'choices': choices})
            module_help = loaded_class.get_module_help()
            collected_doc.append({'module': doc_class.__name__, 'module_help': module_help, 'attributes': class_doc})
        return collected_doc

    @staticmethod
    def format(raw_help_doc: List[Dict[str, List[Dict[str, List[str]]]]]) -> str:
        result: str = ''
        for module_data in raw_help_doc:
            module_help = f"{Style.DIM}<No help provided>{Style.RESET_ALL}" if module_data['module_help'] is None else module_data['module_help']
            result += f'{Style.BRIGHT}{Fore.BLUE}{module_data["module"]}{Fore.RESET}{Style.RESET_ALL}: {module_help}\n'
            for attribute in module_data['attributes']:
                defaults: str = "" if attribute['defaults'] is None else f" Defaults to {Fore.MAGENTA}{attribute['defaults']}{Fore.RESET}."
                choices: str = "" if attribute['choices'] is None else f" Choices are: {Fore.LIGHTBLUE_EX}{attribute['choices']}{Fore.RESET}."
                if attribute['help'] is not None:
                    attribute_name = f'{Fore.WHITE},{Fore.YELLOW} --'.join(attribute['parameter']).replace("_", "-")
                    result += f'\t{Style.BRIGHT}{Fore.YELLOW}--{attribute_name}{Fore.RESET}{Style.RESET_ALL}: {attribute["help"]}.{defaults}{choices}\n'
        return result

    @staticmethod
    def format_default(default_value: any) -> str:
        if callable(default_value):
            return "value calculated in the runtime"
        if isinstance(default_value, list):
            return " ".join(default_value)
        return str(default_value)

    @staticmethod
    def format_choices(rule: Rule) -> str | None:
        choices_key = [key for key, value in VALIDATORS.items() if value == ValueValidator]
        choice_key = [key for key in rule if key in choices_key]
        if not choice_key:
            return None
        choice_value = rule[next(iter(choice_key))]
        if callable(choice_value):
            return "value calculated in the runtime"
        if isinstance(choice_value, list):
            return "[" + ", ".join(choice_value) + "]"
        return str(choice_value)
