from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from solgreen.contracts.import_batch import ImportBatch
from solgreen.diagnostics.llm_output import LLMInterpretation
from solgreen.diagnostics.rule import RuleExecution
from solgreen.timeline.canonical import CanonicalSample
from solgreen.timeline.episode import CanonicalEpisode


class Repository(ABC):
    @abstractmethod
    def save_import_batch(self, batch: ImportBatch) -> None: ...

    @abstractmethod
    def get_import_batch(self, batch_id: UUID) -> ImportBatch | None: ...

    @abstractmethod
    def list_import_batches(self, plant_id: str) -> list[ImportBatch]: ...

    @abstractmethod
    def save_canonical_samples(self, batch_id: UUID, samples: list[CanonicalSample]) -> None: ...

    @abstractmethod
    def get_canonical_samples(self, batch_id: UUID) -> list[CanonicalSample]: ...

    @abstractmethod
    def save_canonical_episode(self, batch_id: UUID, episode: CanonicalEpisode) -> int: ...

    @abstractmethod
    def get_canonical_episodes(self, batch_id: UUID) -> list[CanonicalEpisode]: ...

    @abstractmethod
    def save_rule_execution(self, episode_id: int, execution: RuleExecution) -> None: ...

    @abstractmethod
    def get_rule_executions(self, episode_id: int) -> list[RuleExecution]: ...

    @abstractmethod
    def save_llm_interpretation(
        self, episode_id: int, interpretation: LLMInterpretation
    ) -> None: ...

    @abstractmethod
    def get_llm_interpretations(self, episode_id: int) -> list[LLMInterpretation]: ...
