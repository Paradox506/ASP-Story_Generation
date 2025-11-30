from benchmark.prompt_builders.base_prompt_builder import BasePromptBuilder
from benchmark.prompt_builders.aladdin_prompt_builder import AladdinPromptBuilder
from benchmark.prompt_builders.western_prompt_builder import WesternPromptBuilder
from benchmark.prompt_builders.secret_agent_prompt_builder import SecretAgentPromptBuilder


def get_prompt_builder(domain: str, asp_version: str):
    if domain == "aladdin":
        return AladdinPromptBuilder(domain, asp_version)
    if domain == "western":
        return WesternPromptBuilder(domain, asp_version)
    if domain == "secret_agent":
        return SecretAgentPromptBuilder(domain, asp_version)
    return BasePromptBuilder(domain, asp_version)


__all__ = [
    "get_prompt_builder",
    "BasePromptBuilder",
    "AladdinPromptBuilder",
    "WesternPromptBuilder",
    "SecretAgentPromptBuilder",
]
