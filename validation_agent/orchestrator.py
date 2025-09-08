# -*- coding: utf-8 -*-
from typing import Callable, Dict
from pathlib import Path
from .metrics_loader import load_scoring_profile
from .scorecard import compute_score

class PromptOrchestrator:
    """
    Генерация ответа по промту + self-score (внутри ответа),
    затем локальная оценка по метрикам, затем вызов Критика для TARGET-SCORE.
    """

    def __init__(
        self,
        llm_generate_fn: Callable[[str, Dict], str],
        llm_critic_fn: Callable[[str, str, Dict], Dict],
        config_dir: Path = None
    ):
        self.generate = llm_generate_fn
        self.critic = llm_critic_fn
        self.config_dir = config_dir

    def run(self, *, profile_name: str, prompt_text: str, context: Dict, target_score: float = 9.0) -> Dict:
        # 1) генерация
        answer = self.generate(prompt_text, context)

        # 2) локальная оценка (presence+quality)
        prof = load_scoring_profile(profile_name, base_path=(self.config_dir / "scoring.yaml") if self.config_dir else None)
        local = compute_score(answer, prof)

        # 3) критик — итоговый TARGET-SCORE и комментарий
        critic_output = self.critic(profile_name, answer, prof)

        # Вариант: можно предпринять 1–2 итерации улучшения, если score < target_score
        return {
            "answer": answer,
            "local_score": local,
            "critic": critic_output
        }
