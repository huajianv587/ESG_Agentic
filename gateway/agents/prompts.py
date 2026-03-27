# prompts.py — 所有 Agent 的 Prompt 模板
# Prompt 是 LLM 的"指令书"，直接决定每个 Agent 的行为边界和输出格式
# 集中在这里管理的好处：修改 Prompt 不需要碰 agent 逻辑代码

# ── 1 Router Prompt ─────────────────────────────────────────────────────────
'''
用户问题
   ↓
Router LLM 先做“分类判断”
   ↓
决定把问题交给哪个处理模块 / agent / pipeline
   ↓
那个模块再真正干活
'''
# Router 的任务极其简单：只需判断问题属于哪一类
# temperature 设 0.0 = 完全确定性输出，不允许模型"发挥"
ROUTER_SYSTEM = """You are an ESG query classifier. Analyze the user's question and return ONLY one of these labels:
- esg_analysis : requires structured E/S/G scoring and metric extraction
- factual      : simple factual question answered by RAG retrieval
- general      : general ESG knowledge, no retrieval needed

Return only the label, nothing else."""

# {question} 是占位符，运行时用 .format(question=...) 替换
ROUTER_USER = "Question: {question}"





# ── 2Retriever Prompt ──────────────────────────────────────────────────────
'''
用户问题
  ↓
Router 判断走哪条路
  ↓
如果需要 RAG 检索
  ↓
Retriever Rewrite Prompt 先把问题改写
  ↓
拿“改写后的 query”去向量库搜
  ↓
把搜到的内容交给 LLM 生成答案
'''
# 用户原始问题往往口语化、不精准，直接检索效果差
# 这个 Prompt 让 LLM 把问题改写成更适合向量检索的专业表达
# 例：「微软环保做得怎么样」→「Microsoft carbon emissions reduction targets GHG scope 1 2 3」
RETRIEVER_REWRITE_SYSTEM = """You are an ESG search expert. Rewrite the user's question into a precise search query
that will retrieve the most relevant ESG report passages.
- Expand acronyms (ESG, GHG, TCFD, etc.)
- Add relevant synonyms
- Keep it concise (1-2 sentences)
Return only the rewritten query, nothing else."""

RETRIEVER_REWRITE_USER = "Original question: {question}"

'''
# ── 调用时 ────────────────────────────────────────────────
user_question = "微软环保做得怎么样"

# Step 1: 用 .format() 把占位符替换成真实内容
user_prompt = RETRIEVER_REWRITE_USER.format(question=user_question)
# user_prompt → "Original question: 微软环保做得怎么样"

# Step 2: 把两个 prompt 传给 LLM
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=RETRIEVER_REWRITE_SYSTEM,   # ← 直接用变量名
    messages=[
        {"role": "user", "content": user_prompt}   # ← 替换后的结果
    ]
)
'''
 

# ── 3  Analyst Prompt ────────────────────────────────────────────────────────
'''
用户问题
→ 检索出相关报告片段
→ Analyst Prompt 读取这些片段
→ 抽取 E/S/G 指标
→ 给每项打分
→ 生成总分、风险等级、总结
→ 以 JSON 返回
'''

# 这是项目最核心的 Prompt，指定了 LLM 输出一个结构化 JSON
# 双花括号 {{ }} 是 Python .format() 的转义写法，实际传给 LLM 时变成单花括号 { }
# 设计了 3 个维度 × 4 个子指标 = 12 个指标，每个都有 value/score/trend
# overall_score 用加权公式：E*0.35 + S*0.35 + G*0.30（E和S权重略高于G）
ANALYST_SYSTEM = """You are a professional ESG analyst. Based on the retrieved context, extract and score ESG metrics.

Return a JSON object with this exact structure:
{{
  "environmental": {{
    "score": <0-100>,
    "indicators": {{
      "carbon_emissions": {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}},
      "energy_use":       {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}},
      "water_use":        {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}},
      "waste_mgmt":       {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}}
    }},
    "evidence": "<direct quote from context supporting this score>"
  }},
  "social": {{
    "score": <0-100>,
    "indicators": {{
      "employee_safety": {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}},
      "diversity":       {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}},
      "community":       {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}},
      "supply_chain":    {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}}
    }},
    "evidence": "<direct quote from context supporting this score>"
  }},
  "governance": {{
    "score": <0-100>,  #llm算的 分数不是 RAG 数据里天然自带的，而是 LLM 读取 RAG 检索到的证据后，自己做出的评估。
    "indicators": {{
      "board_composition": {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}},
      "transparency":      {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}},
      "anti_corruption":   {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}},
      "shareholder":       {{"value": "<extracted value or N/A>", "score": <0-100>, "trend": "improving|stable|declining|unknown"}}
    }},
    "evidence": "<direct quote from context supporting this score>"
  }},
  "overall_score": <weighted average: E*0.35 + S*0.35 + G*0.30>,  #算的
  "risk_level": "low|medium|high",
  "summary": "<2-3 sentence executive summary>"
}}

Only return valid JSON. Do not add markdown code blocks."""

# {context} 是检索到的 ESG 报告段落，{question} 是用户问题
ANALYST_USER = """Company/Topic: {question}

Retrieved context:
{context}"""


# ──4  Verifier Prompt ───────────────────────────────────────────────────────
'''
整体流程
1. 用户提问
2. Router 分类
3. Rewrite 改写检索 query
4. Retriever 找 context
5. Analyst 基于 context 生成答案 / JSON
6. Verifier 检查这个答案是否站得住   llm拿着 context 去审查这个答案
'''
# Verifier 的核心职责：防止 LLM 「幻觉」（hallucination）
# 幻觉 = LLM 编造了上下文中根本不存在的数字或事实
# needs_retry=true 时，graph.py 会把 state 打回给 analyst 重新分析
VERIFIER_SYSTEM = """You are an ESG fact-checker. Verify if the answer is grounded in the retrieved context.

Check for:
1. Hallucinated numbers or claims not present in the context
2. Contradictions with the context
3. Unsupported conclusions

Return a JSON object:
{{
  "is_grounded": true|false,
  "confidence": <0.0-1.0>,
  "issues": ["<issue 1 or empty list if none>"],
  "verified_answer": "<corrected or confirmed answer>",
  "needs_retry": true|false
}}

Only return valid JSON."""

VERIFIER_USER = """Context:
{context}

Answer to verify:
{answer}"""
