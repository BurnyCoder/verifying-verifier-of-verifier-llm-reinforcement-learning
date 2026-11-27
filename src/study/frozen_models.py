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
                "Qwen3.8-27B-UD-IQ2_XS.gguf", "be3842ebaaaf8412e434ce856cb05abb0ae9033494c61bff09b289a90d7f7f8e", 7625883648),
)

# Select compression by verified GPU fit before scoring. The screen never selects a quantizer by accuracy.
SMALLER_FILES = {
    "q35-9b": (
        ("Qwen3.5-9B-UD-IQ3_XXS.gguf", "40d0f32cd3030b04f0784139a589fb63e876cfbf8667d56311b79783c74fd149", 4016235744),
        ("Qwen3.5-9B-UD-IQ2_M.gguf", "a31b6b4c603ddd66b5496ee065c9dd13b2b6de77dce9e5d59609aef8d39868e7", 3649365216)),
    "q38-27b": (
        ("Qwen3.8-27B-UD-IQ2_XXS.gguf", "f51f7340110329e897623338c9458544a88a76bfbc360808c847b8d8d0277a6c", 7206043648),
        ("Qwen3.8-27B-UD-IQ1_M.gguf", "1b5165a7149ea51e683c8eaf23372188ad9fc9d1a795386f7a1b558acf847dc6", 6729166848),
        ("Qwen3.8-27B-UD-IQ1_S.gguf", "3895b6eaa91e705c06ad1938d16c22e86f073c6a67df86260a1da79be3d1f887", 6192222208)),
}

# Deployment replicates from an independent packager, outside the registered model-selection pool.
LOCAL_REPLICATES = (
    FrozenModel("q35-9b-ollama","Qwen3.5-9B",MODELS[2].base_revision,"ollama/library/qwen3.5",
                "56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90",
                "Ollama-Qwen3.5-9B-Q4_K_M.gguf","02d45dc1cf451ba2475ac33b301c2dd8f985abe4c182ce04a1f2f5bf0260278d",5629109120),
    FrozenModel("q35-4b-ollama","Qwen3.5-4B",MODELS[1].base_revision,"ollama/library/qwen3.5",
                "d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04",
                "Ollama-Qwen3.5-4B-Q4_K_M.gguf","a9d0a3e1d8c91732a3812becd31f8d4a8ff57414903f226306069f0437e2ac50",2648593216),
)
