"""Revisions fixed before the cross-model study. GGUF digests come from the Hub LFS metadata."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FrozenModel:
    key: str
    title: str
    base_revision: str
    repository: str
    revision: str
    filename: str
    sha256: str
    size: int


MODELS = (
    FrozenModel("q25-1p5b", "Qwen2.5-1.5B-Instruct", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
                "Qwen/Qwen2.5-1.5B-Instruct-GGUF", "91cad51170dc346986eccefdc2dd33a9da36ead9",
                "qwen2.5-1.5b-instruct-q4_k_m.gguf", "6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e", 1117320736),
    FrozenModel("q35-4b", "Qwen3.5-4B", "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
                "unsloth/Qwen3.5-4B-GGUF", "e87f176479d0855a907a41277aca2f8ee7a09523",
                "Qwen3.5-4B-Q4_K_M.gguf", "00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4", 2740937888),
    FrozenModel("q35-9b", "Qwen3.5-9B", "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
                "unsloth/Qwen3.5-9B-GGUF", "3885219b6810b007914f3a7950a8d1b469d598a5",
                "Qwen3.5-9B-Q4_K_M.gguf", "03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8", 5680522464),
    FrozenModel("q38-27b", "Qwen3.8-27B", "37561816e66b5b9153b1b64c10968c18c1e6f4a0",
                "unsloth/Qwen3.8-27B-GGUF", "4af51b3542f775b0a8e4b310bfb3f17e01c306c9",
                "Qwen3.8-27B-UD-Q4_K_M.gguf", "1bce504dfecd84153666928a41d8a66706f0158d3a317bc5196b72819d7dc529", 16564259744),
)
