import abc
from abc import ABC, abstractmethod
from contexts import GlobalContext as GlobalContext
from dagger import Client as Client, Container as Container
from datetime import datetime
from enum import Enum
from rich.style import Style
from typing import Any, ClassVar, Optional, Union

class StepStatus(Enum):
    SUCCESS: str
    FAILURE: str
    SKIPPED: str
    def from_exit_code(self, exit_code: int) -> StepStatus: ...
    def get_rich_style(self) -> Style: ...

class Step(ABC, metaclass=abc.ABCMeta):
    title: ClassVar
    context: Any
    def __init__(self, context: GlobalContext) -> None: ...
    @abstractmethod
    async def run(self) -> StepResult: ...
    def skip(self, reason: Optional[str] = ...) -> StepResult: ...
    def get_dagger_pipeline(self, dagger_client_or_container: Union[Client, Container]) -> Union[Client, Container]: ...
    async def get_step_result(self, container: Container) -> StepResult: ...

class StepResult:
    step: Step
    status: StepStatus
    created_at: datetime
    stderr: Optional[str]
    stdout: Optional[str]
    def __init__(self, step: Step, status: StepStatus, created_at: datetime, stderr: str, stdout: str) -> None: ...
