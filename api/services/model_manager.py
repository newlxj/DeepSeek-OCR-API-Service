"""
模型管理器 - 单例模式，延迟加载
"""
import os
from typing import Optional

import torch
if torch.version.cuda == '11.8':
    os.environ["TRITON_PTXAS_PATH"] = "/usr/local/cuda-11.8/bin/ptxas"

os.environ['VLLM_USE_V1'] = '0'

from vllm import LLM, SamplingParams
from vllm.model_executor.models.registry import ModelRegistry
from deepseek_ocr2 import DeepseekOCR2ForCausalLM
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
from config import MODEL_PATH, MAX_CONCURRENCY

# 注册自定义模型
ModelRegistry.register_model("DeepseekOCR2ForCausalLM", DeepseekOCR2ForCausalLM)


class ModelManager:
    """
    模型管理器 - 单例模式，延迟加载

    只有在第一次调用时才加载模型，避免服务启动时占用大量内存
    使用统一的同步引擎处理所有任务（单图/批量/PDF）
    """

    _instance: Optional['ModelManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._llm: Optional[LLM] = None
        self._sampling_params: Optional[SamplingParams] = None
        self._loading = False
        self._initialized = True

    def get_llm(self) -> LLM:
        """
        获取LLM引擎（延迟加载）

        Returns:
            LLM: vLLM推理引擎
        """
        if self._llm is None:
            print("Loading LLM (first call)...")
            self._llm = self._load_llm()
            self._sampling_params = self._create_sampling_params()
            print("LLM loaded successfully")
        return self._llm

    def _load_llm(self) -> LLM:
        """
        加载LLM引擎

        Returns:
            LLM
        """
        return LLM(
            model=MODEL_PATH,
            hf_overrides={"architectures": ["DeepseekOCR2ForCausalLM"]},
            block_size=256,
            enforce_eager=False,
            trust_remote_code=True,
            max_model_len=8192,
            swap_space=0,
            max_num_seqs=MAX_CONCURRENCY,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.9,
            disable_mm_preprocessor_cache=True
        )

    def _create_sampling_params(self) -> SamplingParams:
        """
        创建采样参数

        Returns:
            SamplingParams
        """
        logits_processors = [
            NoRepeatNGramLogitsProcessor(
                ngram_size=20,
                window_size=50,
                whitelist_token_ids={128821, 128822}  # <td>, </td>
            )
        ]

        return SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            logits_processors=logits_processors,
            skip_special_tokens=False,
            include_stop_str_in_output=True,
        )

    def get_sampling_params(self) -> SamplingParams:
        """
        获取采样参数

        Returns:
            SamplingParams
        """
        return self._sampling_params or self._create_sampling_params()

    def is_loaded(self) -> bool:
        """
        检查模型是否已加载

        Returns:
            bool: 是否已加载
        """
        return self._llm is not None


# 全局模型管理器实例
model_manager = ModelManager()
