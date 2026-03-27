from __future__ import annotations

import torch
from openai import OpenAI
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

from gateway.config import settings
from gateway.utils.logger import get_logger

logger = get_logger(__name__)

# 项目根目录和模型路径配置
PROJECT_ROOT  = Path(__file__).resolve().parents[3]
LOCAL_CKPT    = str(PROJECT_ROOT / "model-serving" / "checkpoints")
LOCAL_BASE    = "Qwen/Qwen2.5-7B-Instruct"
MAX_LOCAL_FAILURES = 3   # 连续失败超过这个数就切到云端

# ── 单例变量 ──────────────────────────────────────────────────────────────────
_local_model     = None  # 本地模型实例（避免重复加载）
_local_tokenizer = None  # 本地分词器实例
_openai_client   = None  # OpenAI 客户端实例
_deepseek_client = None  # DeepSeek 客户端实例
_local_fail_count = 0    # 本地模型连续失败计数器（熔断器）


# ── 本地模型 ──────────────────────────────────────────────────────────────

def _load_local_model():
    """
    加载本地 LoRA 微调模型（单例模式）。
    
    流程：
    1. 检查是否已加载（单例）
    2. 加载基座模型 Qwen2.5-7B
    3. 加载 LoRA 适配器
    4. 设置为评估模式
    """
    global _local_model, _local_tokenizer
    if _local_model is not None:
        return _local_model, _local_tokenizer

    ckpt = Path(LOCAL_CKPT)
    if not ckpt.exists():
        raise FileNotFoundError(f"Local checkpoint not found: {LOCAL_CKPT}")

    logger.info(f"[LLM] Loading local model from {LOCAL_CKPT} ...")
    # 加载分词器
    tokenizer = AutoTokenizer.from_pretrained(LOCAL_BASE, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    # 加载基座模型（float16 精度，自动分配设备）
    model = AutoModelForCausalLM.from_pretrained(
        LOCAL_BASE,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    # 加载 LoRA 适配器
    model = PeftModel.from_pretrained(model, LOCAL_CKPT)
    model.eval()  # 设置为评估模式

    _local_model, _local_tokenizer = model, tokenizer
    logger.info("[LLM] Local model ready.")
    return model, tokenizer


def _chat_local(messages: list[dict], max_new_tokens: int = 1024) -> str:
    """
    使用本地模型进行推理。
    
    Args:
        messages: 对话消息列表，格式 [{"role": "user", "content": "..."}]
        max_new_tokens: 最大生成 token 数
    
    流程：
    1. 使用 chat_template 格式化 messages → prompt 字符串
    2. tokenize 编码 → input_ids + attention_mask
    3. 模型推理生成
    4. 解码新生成的 token（排除输入部分）
    """
    model, tokenizer = _load_local_model()
    # 将 messages 格式化为 prompt 字符串
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    # tokenize 编码为 input_ids 和 attention_mask
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # 贪婪解码（确定性输出）
            pad_token_id=tokenizer.eos_token_id,
        )
    # 只解码新生成的部分（排除输入 prompt）
    new_ids = output_ids[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(new_ids, skip_special_tokens=True).strip()


# ── 云端客户端 ────────────────────────────────────────────────────────────

def _get_openai_client() -> OpenAI:
    """获取 OpenAI 客户端（单例）。"""
    global _openai_client
    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set in .env")
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _get_deepseek_client() -> OpenAI:
    """获取 DeepSeek 客户端（单例，使用 OpenAI SDK 兼容接口）。"""
    global _deepseek_client
    if _deepseek_client is None:
        if not settings.DEEPSEEK_API_KEY:
            raise RuntimeError("DEEPSEEK_API_KEY not set in .env")
        _deepseek_client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
        )
    return _deepseek_client


def _chat_openai(messages: list[dict], max_tokens: int = 1024, temperature: float = 0.2) -> str:
    """
    调用 OpenAI GPT-4o API。
    
    Args:
        messages: 对话消息列表
        max_tokens: 最大生成 token 数
        temperature: 温度参数（0.0=确定性，1.0+=高随机性）
    """
    client = _get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def _chat_deepseek(messages: list[dict], max_tokens: int = 1024, temperature: float = 0.2) -> str:
    """
    调用 DeepSeek API（兜底方案）。
    
    Args:
        messages: 对话消息列表
        max_tokens: 最大生成 token 数
        temperature: 温度参数
    """
    client = _get_deepseek_client()
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


# ── 统一入口（带 fallback 链）────────────────────────────────────────────

def chat(
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> str:
    """
    统一 LLM 调用接口，带三级 fallback 机制。
    
    调用链：本地 LoRA 模型 → OpenAI GPT-4o → DeepSeek
    
    Args:
        messages: 对话消息列表，格式：
                  [{"role": "system", "content": "你是ESG助手"},
                   {"role": "user", "content": "什么是ESG？"}]
        temperature: 温度参数，控制随机性（0.0-1.0+）
                     0.2 适合分析任务（稳定输出）
        max_tokens: 最大生成 token 数（约 1 token ≈ 0.5 个中文字）
    
    Returns:
        生成的文本回复
    
    熔断机制：
        本地模型连续失败 3 次后自动切换到云端
    
    用法:
        from gateway.utils.llm_client import chat
        reply = chat([{"role": "user", "content": "What is ESG?"}])
    """
    global _local_fail_count

    # ── 1. 本地 LoRA 模型 ────────────────────────────────────────────────
    if _local_fail_count < MAX_LOCAL_FAILURES:
        try:
            result = _chat_local(messages, max_new_tokens=max_tokens)
            _local_fail_count = 0   # 成功则重置计数
            return result
        except Exception as e:
            _local_fail_count += 1
            logger.warning(
                f"[LLM] Local model failed ({_local_fail_count}/{MAX_LOCAL_FAILURES}): {e}"
            )
            if _local_fail_count >= MAX_LOCAL_FAILURES:
                logger.error("[LLM] Local model disabled after repeated failures, switching to cloud.")
    else:
        logger.debug("[LLM] Local model skipped (too many failures), using cloud.")

    # ── 2. OpenAI GPT-4o ────────────────────────────────────────────────
    try:
        result = _chat_openai(messages, max_tokens=max_tokens, temperature=temperature)
        logger.info("[LLM] Response from OpenAI GPT-4o.")
        return result
    except Exception as e:
        logger.warning(f"[LLM] OpenAI failed: {e}, falling back to DeepSeek.")

    # ── 3. DeepSeek（最后兜底）──────────────────────────────────────────
    try:
        result = _chat_deepseek(messages, max_tokens=max_tokens, temperature=temperature)
        logger.info("[LLM] Response from DeepSeek.")
        return result
    except Exception as e:
        logger.error(f"[LLM] All LLM backends failed. Last error: {e}")
        raise RuntimeError("All LLM backends failed.") from e
