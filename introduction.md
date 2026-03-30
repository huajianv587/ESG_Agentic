
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           ESG AGENTIC RAG COPILOT - 完整项目讲解与理解指南                      ║
║                                                                              ║
║  作者: Claude Code 初版 → 用户理解与掌握版本                                    ║
║  日期: 2026-03-29                                                            ║
║  版本: 1.0.0 Enhancement Release                                             ║
║                                                                              ║
║  核心目标: 从"Claude生成的代码" → "用户能理解和掌握的代码"                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

这个文件的用途：
- 📚 项目全景地图：了解整个项目的结构和关系
- 🔍 深度理解：理解每个文件、函数、类的具体作用
- 📊 流程可视化：通过流程图理解数据和控制流
- 💡 代码讲解：每行代码的含义和为什么这样写
- 🐛 问题检查：发现和修复潜在的问题
- 🚀 优化方向：规划Multi-Agent升级路径

================================================================================
第一部分：项目全景结构地图
================================================================================

【项目顶层结构】

ESG-Agentic-RAG-Copilot/
│
├─ 📁 configs/                          【全局配置】
│  └─ config.py                         LLM、数据库、邮件等全局参数配置
│
├─ 📁 gateway/                          【主应用核心】- 整个系统的心脏
│  │
│  ├─ 📁 agents/                        【Agent工作流引擎】- 智能分析的大脑
│  │  ├─ graph.py                       ⭐ LangGraph工作流编排（路由→检索→分析→验证）
│  │  ├─ router_agent.py                问题分类：ESG分析 vs 事实查询 vs 通用知识
│  │  ├─ retriever_agent.py             RAG检索：向量相似度搜索 + 缓存管理
│  │  ├─ analyst_agent.py               结构化分析：12个指标评分 + JSON输出
│  │  ├─ verifier_agent.py              验证和幻觉检测：置信度评估
│  │  ├─ esg_scorer.py                  ✨【新】15维度ESG评分框架 (E/S/G各5个)
│  │  ├─ esg_visualizer.py              ✨【新】6种图表可视化生成
│  │  ├─ prompts.py                     所有Agent的系统提示词
│  │  └─ tools.py                       外部工具调用接口
│  │
│  ├─ 📁 rag/                           【RAG检索增强引擎】- 知识库连接
│  │  ├─ rag_main.py                    ⭐ RAG主入口：初始化和查询
│  │  ├─ ingestion.py                   数据摄入：从文件到向量库
│  │  ├─ indexing.py                    索引构建：文档分块和向量化
│  │  ├─ chunking.py                    分块策略：文本分割为合适大小
│  │  ├─ retriever.py                   检索器：向量相似度搜索
│  │  ├─ evaluator.py                   RAG评估：检索质量评分
│  │  └─ cache.py                       缓存层：加速重复查询
│  │
│  ├─ 📁 scheduler/                     【主动分析调度系统】- 定时自动分析
│  │  ├─ orchestrator.py                ⭐ 流程编排：协调5个模块的完整流程
│  │  ├─ scanner.py                     数据扫描：从新闻/报告源发现事件
│  │  ├─ event_extractor.py             事件提取：使用LLM结构化提取信息
│  │  ├─ risk_scorer.py                 风险评分：AI驱动的0-100评分
│  │  ├─ matcher.py                     事件匹配：精准匹配用户偏好
│  │  ├─ notifier.py                    推送通知：Email/In-app/Webhook
│  │  ├─ data_sources.py                ✨【新】多源数据融合 (Alpha Vantage等)
│  │  ├─ report_generator.py            ✨【新】日/周/月报告自动生成
│  │  ├─ report_scheduler.py            ✨【新】定时调度和智能推送
│  │  └─ __init__.py                    模块导出
│  │
│  ├─ 📁 db/                            【数据库层】- 数据持久化
│  │  └─ supabase_client.py             Supabase连接：单例模式+会话管理
│  │
│  ├─ 📁 models/                        【数据模型】- 类型定义
│  │  └─ schemas.py                     Pydantic模型：事件、评分、通知等
│  │
│  ├─ 📁 utils/                         【通用工具库】- 公共函数
│  │  ├─ llm_client.py                  LLM调用：Claude/GPT-4/DeepSeek Fallback链
│  │  ├─ logger.py                      日志管理：结构化日志输出
│  │  ├─ cache.py                       缓存工具：Redis/Memory/File
│  │  └─ retry.py                       重试机制：指数退避+熔断器
│  │
│  ├─ main.py                           原始API入口 (被动查询)
│  └─ main_enhanced.py                  ✨【新】增强API入口 (包含18个新端点)
│
├─ 📁 training/                         【模型微调】- 本地模型优化 (可选)
│  ├─ finetune.py                       LoRA微调流程
│  ├─ prepare_data.py                   训练数据准备
│  ├─ evaluate_model.py                 模型评估
│  ├─ launch_job.py                     远程任务启动 (EC2)
│  └─ upload_data.py                    上传数据到云
│
├─ 📁 data/                             【数据目录】
│  └─ scripts/                          数据处理脚本
│     ├─ alpha_vantage_data.py          从Alpha Vantage获取股价数据
│     ├─ parse_esg.py                   解析ESG报告
│     └─ row_data.py                    原始数据处理
│
├─ 📁 migrations/                       【数据库迁移脚本】
│  ├─ 001_initial_schema.sql            初始表结构
│  ├─ 002_scheduler_tables.sql          调度器相关表
│  └─ 003_add_esg_report_tables.sql     ✨【新】报告系统表
│
├─ 📁 model-serving/                    【模型服务】(可选)
│
├─ 📄 .env.example                      ✨【新】环境配置模板 (40+ API Key说明)
├─ 📄 .env                              实际配置文件 (git忽略)
├─ 📄 requirements.txt                  项目依赖列表
│
├─ 📄 API_ENDPOINTS.md                  ✨【新】完整API文档 (18个端点)
├─ 📄 DEPLOYMENT_GUIDE.md               ✨【新】详细部署指南
├─ 📄 QUICK_START.md                    ✨【新】5分钟快速开始
├─ 📄 ENHANCEMENT_PLAN.md               ✨【新】系统增强方案
├─ 📄 IMPLEMENTATION_SUMMARY.md         项目完成总结
├─ 📄 SCHEDULER_README.md               调度器使用指南
├─ 📄 PROJECT_COMPLETION_SUMMARY.md     ✨【新】项目完成报告
├─ 📄 DATA_SOURCE_REPLACEMENT_GUIDE.md  ✨【新】数据源替换指南
│
└─ 📄 introduction.py                   ✨【新】本文件 - 项目全景讲解

================================================================================
第二部分：核心流程详解
================================================================================

【整个项目的2大工作模式】

┌────────────────────────────────────────────────────────────────────────┐
│  模式1️⃣: 被动分析（用户主动查询）                                      │
│  ═════════════════════════════════════════════════════════════════════ │
│                                                                        │
│  User Question                                                         │
│      ↓                                                                 │
│  Router Agent        分类问题：ESG分析 vs 事实查询                      │
│      ↓                                                                 │
│  Retriever Agent     RAG检索：向量库相似度搜索                          │
│      ↓                                                                 │
│  Analyst Agent       ⭐ 新增：ESG Scorer → 15维度评分                   │
│      ↓                                                                 │
│  Visualizer          ⭐ 新增：生成6种可视化图表                         │
│      ↓                                                                 │
│  Verifier Agent      验证和置信度评估                                   │
│      ↓                                                                 │
│  Response            返回答案 + 评分 + 可视化数据                       │
│                                                                        │
│  【关键文件】: graph.py → analyst_agent.py → esg_scorer.py            │
│  【耗时】: 2-5秒 (受LLM速率限制)                                      │
│  【API端点】: POST /agent/analyze, POST /agent/esg-score              │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│  模式2️⃣: 主动分析（系统定期自动推送）                                  │
│  ═════════════════════════════════════════════════════════════════════ │
│                                                                        │
│  定时触发 (06:00/08:00/09:00)                                          │
│      ↓                                                                 │
│  DataSourceManager    ⭐ 新增：多源数据融合                            │
│      ↓ (Alpha V/Hyfinnan/SEC/NewsAPI/Finnhub)                         │
│  ReportGenerator      ⭐ 新增：生成日/周/月报告                        │
│      ↓                                                                 │
│  ReportScheduler      ⭐ 新增：定时调度                                │
│      ↓                                                                 │
│  PushRules引擎        ⭐ 新增：智能推送规则匹配                        │
│      ↓                                                                 │
│  Notifier             推送通知给用户                                    │
│      ↓                                                                 │
│  Database             存储报告和推送历史                                │
│                                                                        │
│  【关键文件】: report_scheduler.py → report_generator.py →             │
│              data_sources.py → orchestrator.py                        │
│  【调度时间】:                                                          │
│    - 日报: 每日06:00 (新闻摘要 + 风险预警)                             │
│    - 周报: 每周一08:00 (评分变化 + 行业对标)                           │
│    - 月报: 每月1日09:00 (投资组合视图)                                 │
│  【API端点】: POST /admin/reports/generate, /admin/push-rules等       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘


【2大模式的数据流关系】

        User Input              Scheduled Tasks
             ↓                         ↓
        ┌─────────────────────────────────────┐
        │    DataSourceManager (多源融合)      │
        │  Alpha/Hyfinnan/SEC/News/Finnhub   │
        └─────────────────────────────────────┘
             ↓                         ↓
        ┌─────────────────────────────────────┐
        │    ESGScoringFramework (15维度评分)  │
        │         (E/S/G各5个指标)             │
        └─────────────────────────────────────┘
             ↓                         ↓
        ┌─────────────────────────────────────┐
        │    ESGVisualizer (6种可视化)        │
        │    + ReportGenerator (报告生成)     │
        └─────────────────────────────────────┘
             ↓                         ↓
        ┌─────────────────────────────────────┐
        │    PushRules引擎 + Notifier (推送)  │
        │         Email/In-app/Webhook       │
        └─────────────────────────────────────┘
             ↓                         ↓
        用户返回答案                  用户收到报告
        (实时)                        (定时推送)

================================================================================
第三部分：关键文件深度讲解
================================================================================

【重点1】gateway/agents/graph.py - LangGraph工作流编排
────────────────────────────────────────────────────────────────────────

这是整个Agent系统的"总指挥"，定义了问题从输入到输出的完整流程。

⭐ 工作流步骤：
  1. Router Agent      → 问题分类 (什么类型的问题?)
  2. Retriever Agent   → 知识检索 (从RAG库找相关文档)
  3. Analyst Agent     → 深度分析 (提取结构化信息)
  4. Verifier Agent    → 质量检查 (验证答案正确性)

💡 为什么这样设计？
  • Router: 不同问题需要不同的处理策略
  • Retriever: RAG确保答案基于可靠的文献资料
  • Analyst: LLM进行深度理解和推理
  • Verifier: 多次验证，减少LLM的"幻觉"(虚构信息)

🔄 关键概念：LangGraph的条件分支

  if 问题类型 == "ESG分析":
      → 使用 Analyst Agent（15维度评分）
  elif 问题类型 == "事实查询":
      → 使用 Retriever Agent（直接返回文献）
  else:
      → 使用通用 LLM 回答


【重点2】gateway/scheduler/orchestrator.py - 主动分析的大脑
────────────────────────────────────────────────────────────────────────

这个文件协调了整个定时分析流程。如果说graph.py是"被动分析"，
orchestrator.py就是"主动分析"的总指挥。

⭐ 5阶段流程管道：

  第1阶段：Scanner (数据扫描)
    作用: 从新闻API、报告库、法规源发现新事件
    输出: 原始事件列表 (title, description, url)

    代码逻辑:
      for data_source in [news_api, sec_edgar, ...]:
          events = data_source.scan()  # 拉取最新数据
          save_to_db(events)           # 存储到esg_events表

  第2阶段：EventExtractor (事件提取)
    作用: 使用LLM将原始文本转换为结构化数据
    输入: 原始事件
    输出: 结构化事件 (company, event_type, key_metrics, severity)

    代码逻辑:
      for event in raw_events:
          prompt = f"提取这个新闻中的ESG信息: {event.text}"
          structured = llm_call(prompt)  # 让LLM进行结构化提取
          save_to_db(structured)

  第3阶段：RiskScorer (风险评分)
    作用: AI评估事件的风险等级 (0-100分, 分为Low/Medium/High/Critical)
    输入: 结构化事件
    输出: 风险评分 + 推理过程

    代码逻辑:
      for event in extracted_events:
          score = llm_call(f"这个事件的风险有多大? {event}")
          # 例: "特斯拉因工伤被起诉" → High Risk (75分)
          save_to_db(score)

  第4阶段：EventMatcher (事件匹配)
    作用: 根据用户偏好精准匹配事件
    输入: 风险评分 + 用户偏好 (关注的公司、类别、关键词)
    输出: 匹配的事件-用户对

    代码逻辑:
      for event in scored_events:
          for user in all_users:
              if matches_user_preference(event, user.preference):
                  create_match(event_id, user_id)
              # 例: Tesla新闻 → 关注特斯拉的用户

  第5阶段：Notifier (推送通知)
    作用: 将匹配结果推送给用户
    输入: 事件-用户匹配对
    输出: Email/App通知

    代码逻辑:
      for match in event_user_matches:
          notification = format_notification(match)
          send_email(match.user.email, notification)
          save_in_app_notification(match.user.id, notification)

💡 为什么分成5个阶段?
  • 单一职责: 每个模块只做一件事，代码清晰易维护
  • 容错机制: 某个阶段失败不影响其他阶段
  • 可扩展性: 可以轻松添加新的数据源或推送方式
  • 性能优化: 可以独立优化和并行处理

⚡ 性能指标：
  • Scanner: 5-10秒 (取决于数据源)
  • Extractor: 2-3秒/事件 (受LLM速率限制)
  • RiskScorer: 2-3秒/事件
  • Matcher: <1秒 (数据库查询)
  • Notifier: <1秒 (异步推送)
  总耗时: 15-30秒 (对于100个事件)


【重点3】gateway/agents/esg_scorer.py - 结构化ESG评分 ✨【新增】
────────────────────────────────────────────────────────────────────────

这是整个项目最重要的创新：将模糊的"ESG评分"变成15个明确的指标。

⭐ 核心设计：3个维度 × 5个指标 = 15维度评分体系

  环境维度 (E - Environmental):
    1. 碳排放强度          单位: tCO2e/百万收入
       含义: 企业排放了多少CO2，相对于其收入规模
       如何评分: 与同行业平均水平对比
       数据来源: SEC EDGAR 10-K 报告, 企业可持续发展报告

    2. 能源效率            单位: MWh/产出单位
       含义: 生产一个单位的产品需要多少能源
       如何评分: 效率越高，分数越高

    3. 水资源管理          单位: 千升/产出单位
       含义: 水消耗量

    4. 废物管理            单位: 回收率%
       含义: 废物中有多少被回收利用

    5. 可再生能源使用      单位: % of total
       含义: 可再生能源占总能源的比例
       如何评分: 越接近100%，分数越高

  社会维度 (S - Social):
    1. 员工满意度          单位: eNPS score
       含义: 员工愿意推荐公司的程度（-100到100分）

    2. 多样性与包容性      单位: % women/minorities
       含义: 女性和少数族裔员工占比
       为什么重要: 多样性团队有更好的决策和创新

    3. 供应链伦理          单位: 合规率%
       含义: 供应商是否满足劳动标准、环保标准

    4. 社区关系            单位: 投资额/社会影响指数
       含义: 企业对社区的贡献

    5. 客户保护            单位: 投诉率/满意度
       含义: 数据隐私、产品安全

  治理维度 (G - Governance):
    1. 董事会多样性        单位: % 独立董事
       含义: 独立董事是否足够，是否有女性和外部人士

    2. 高管薪酬合理性      单位: 倍数 (CEO薪酬/员工中位数)
       含义: CEO的薪酬与普通员工的差距
       如何评分: 比例越接近（例1倍），分数越高
       为什么重要: 薪酬公平关系到员工满意度

    3. 反腐机制            单位: 得分/10
       含义: 是否有完善的反贿赂、反腐政策

    4. 风险管理            单位: 评级
       含义: 网络安全、业务连续性规划

    5. 股东权益保护        单位: 得分/10
       含义: 股东是否有充分的投票权和信息权

💡 为什么这样分？
  • 每个指标都是可衡量的（有具体的单位和数据来源）
  • 避免模糊的"总体评分"，每个分数都有依据
  • 便于对标：可以与同行业企业比较
  • 便于改进：企业知道具体要改什么

📊 评分算法：

  对于每个维度的评分（例如E维度）：

  E_score = Σ(指标_i × 权重_i) / Σ(权重_i)

  例子：
    碳排放 (80分) × 0.25 = 20
    能源效率 (75分) × 0.20 = 15
    水资源 (70分) × 0.15 = 10.5
    废物管理 (85分) × 0.20 = 17
    可再生能源 (90分) × 0.20 = 18
    ─────────────────────────────
    E维度总分 = (20+15+10.5+17+18) / (0.25+0.20+0.15+0.20+0.20)
             = 80.5 / 1.0
             = 80.5分 (最终E维度得分)

  整体ESG评分 = (E_score × E权重 + S_score × S权重 + G_score × G权重)


【重点4】gateway/agents/esg_visualizer.py - 多维可视化 ✨【新增】
────────────────────────────────────────────────────────────────────────

ESG评分不能只是数字，还要让人一眼看明白。这个模块生成6种图表。

⭐ 6种可视化类型：

  1. 雷达图 (Radar Chart)
     用途: 展示E/S/G三个维度的相对强弱

     例子:
             N (多样性)
              ↑
         E50 |  S75
             | /               |/             ────┼──────┼──── E (能源)
             |\    /
             | \  /
             | G65

     解读: 这家公司社会维度最强(75)，治理次之(65)，
           环境维度最弱(50)，需要加强环保投入

  2. 柱状图 (Bar Charts)
     用途: 展示15个具体指标的详细评分

     E维度详情:
     ┌─────────────────────────────────────┐
     │ 碳排放强度      [████████░] 80      │
     │ 能源效率       [███████░░] 75      │
     │ 水资源管理     [██████░░░] 70      │
     │ 废物管理       [█████████░] 85     │
     │ 可再生能源     [██████████] 90     │
     └─────────────────────────────────────┘

     解读: 可再生能源做得最好，水资源管理需要改进

  3. 热力图 (Heatmap)
     用途: 与行业同行企业对比

     例子 (汽车行业):
                   碳  能源 水资  废  可再
     Tesla    [██████] 85分
     Ford     [█████░] 75分 ← Tesla领先10分
     GM       [████░░] 65分
     BMW      [███████] 90分 ← BMW在这方面更强

     解读: Tesla在大多数指标领先，但碳排放略低于BMW

  4. 仪表盘 (Gauge Charts)
     用途: 展示总体评分进度

     总体ESG评分:
          0      50      100
          ├──────◆│───────┤
                  78/100
               (良好)

     解读: 这家公司的整体ESG水平是"良好"

  5. 趋势图 (Trend Chart)
     用途: 展示一年内评分变化

     例子:
     2025年-2026年趋势:

     分数 ↑
     90   │         ╱──╲
     80   │    ╱──╱    ╲
     70   │───╱          ╲
     60   │                ╲
         └─────────────────── 时间
            1月  3月  6月  9月  12月

     解读: 2026年上半年持续改进，下半年出现下降(可能是新丑闻)

  6. HTML报告
     用途: 可独立查看的完整报告 (不需要API)

     包含: 所有上述图表 + 文字分析 + 改进建议

💡 数据格式（给前端的JSON结构）：

  {
    "radar": {
      "labels": ["环境(E)", "社会(S)", "治理(G)"],
      "datasets": [{
        "label": "Tesla",
        "data": [85, 70, 75],  # 三个维度的分数
        "backgroundColor": "rgba(79,70,229,0.1)"
      }]
    },
    "gauges": [{
      "title": "综合ESG评分",
      "value": 78,          # 当前值
      "max": 100,           # 最大值
      "color": "#10B981"    # 绿色（表示不错）
    }]
  }


【重点5】gateway/scheduler/data_sources.py - 多源数据融合 ✨【新增】
────────────────────────────────────────────────────────────────────────

这个模块是数据"大聚合"，从5个完全不同的来源融合数据。

⭐ 5大数据源及其作用：

  1. Alpha Vantage
     来源: https://www.alphavantage.co/
     获取数据:
       - 股价数据 (日K线、周K线、月K线)
       - 财务数据 (收入、利润、现金流)
       - 技术指标 (PE比、市值、EPS)

     为什么需要:
       • 了解企业的财务健康状况
       • 评估市场对企业的看法
       • 计算财务相关的ESG指标

     代码逻辑:
       resp = requests.get(
           "https://www.alphavantage.co/query",
           params={
               "function": "GLOBAL_QUOTE",
               "symbol": "TSLA",
               "apikey": "xxxxx"
           }
       )
       # 解析响应，提取股价、PE比等
       price = resp.json()["Global Quote"]["05. price"]
       pe_ratio = resp.json()["Global Quote"]["n/a"]

  2. Hyfinnan (或Yahoo Finance)
     来源: https://www.hyfinnan.com/ 或 https://rapidapi.com/
     获取数据:
       - ESG评级 (MSCI、Sustainalytics、Refinitiv)
       - 可持续性报告
       - 第三方ESG评分

     为什么需要:
       • 获取权威的第三方ESG评分
       • 与国际标准对标
       • 验证自己的评分是否合理

     代码逻辑:
       response = requests.get(
           f"https://api.hyfinnan.com/v1/esg/{company_name}",
           headers={"Authorization": f"Bearer {api_key}"}
       )
       esg_rating = response.json()["esg_score"]  # 返回0-100的评分

  3. SEC EDGAR
     来源: https://www.sec.gov/cgi-bin/browse-edgar
     获取数据:
       - 10-K (年报) - 详细的年度报告
       - 10-Q (季报) - 季度报告
       - DEF 14A (代理声明) - 董事薪酬、董事会结构
       - 8-K (重大事件) - 实时信息披露

     为什么需要:
       • 这些是官方、可信的披露
       • 包含治理相关的详细信息
       • 美国上市公司必须披露

     代码逻辑:
       # 搜索公司信息
       response = requests.get(
           "https://www.sec.gov/cgi-bin/browse-edgar",
           params={
               "action": "getcompany",
               "company": "Tesla",
               "count": 10
           },
           headers={"User-Agent": "your_email@example.com"}
       )
       # 解析HTML，获取10-K和10-Q的链接
       # 下载文档，使用NLP提取信息

  4. NewsAPI
     来源: https://newsapi.org/
     获取数据:
       - ESG相关新闻
       - 企业负面新闻 (事故、诉讼)
       - 行业动态

     为什么需要:
       • 捕捉实时的风险信号
       • 了解企业的社会评价
       • 发现新的问题

     代码逻辑:
       response = requests.get(
           "https://newsapi.org/v2/everything",
           params={
               "q": "Tesla ESG",
               "sortBy": "publishedAt",
               "language": "en",
               "apiKey": "xxxxx"
           }
       )
       articles = response.json()["articles"]
       for article in articles:
           title = article["title"]
           url = article["url"]
           published_date = article["publishedAt"]

  5. Finnhub
     来源: https://finnhub.io/
     获取数据:
       - 企业概览信息
       - 高管信息
       - 行业分类
       - 股价和市值

     为什么需要:
       • 企业基本信息
       • 领导人背景
       • 行业对标

⚡ 数据融合的关键：数据清洗和去重

  问题: 5个来源可能提供的数据不一致
  解决:

    1. 时间对齐: 确保都是最新数据
       if alpha_vantage_date < hyfinnan_date < 24_hours_ago:
           flag_as_outdated()

    2. 值验证: 检查数据是否合理
       if revenue_2025 < revenue_2024:
           flag_as_suspicious()  # 收入下降可能是真实，也可能是数据错误

    3. 权重分配: 不同来源的数据权重不同
       final_esg_score = (
           alpha_vantage_data × 0.2 +    # 财务数据，权重20%
           hyfinnan_data × 0.4 +         # ESG数据，权重40% (最重要)
           sec_data × 0.2 +              # 官方披露，权重20%
           news_data × 0.1 +             # 新闻，权重10%
           finnhub_data × 0.1            # 其他，权重10%
       )

================================================================================
第四部分：代码注释示例与讲解
================================================================================

【示例1】如何理解Router Agent的代码逻辑

原始代码（缺乏注释）:
────────────────────

def run_router(state: dict) -> dict:
    question = state["question"]
    messages = [
        {"role": "system", "content": ROUTER_SYSTEM},
        {"role": "user", "content": f"问题: {question}"},
    ]
    response = chat(messages, temperature=0.1)
    choice = response.strip()
    next_node = choice.split(":")[1].strip()
    return {**state, "route": next_node}

为什么这样写？- 详细讲解版：
────────────────────────────

def run_router(state: dict) -> dict:
    # 💡 state是一个字典，包含用户的问题和之前处理的结果
    # 例: {"question": "分析特斯拉的ESG表现", "session_id": "xxx"}
    question = state["question"]

    # 🤖 构建发送给LLM的消息
    # 消息由两部分组成：
    #   1. system: 告诉LLM它的角色和职责
    #   2. user: 实际的问题
    messages = [
        {"role": "system", "content": ROUTER_SYSTEM},
        # ROUTER_SYSTEM的内容是什么？在prompts.py中定义:
        # "你是一个问题分类器。根据问题类型，选择处理方式。
        #  - 如果是ESG分析问题，回复 'Route: esg_analysis'
        #  - 如果是事实查询，回复 'Route: fact_check'
        #  - 其他，回复 'Route: general'"

        {"role": "user", "content": f"问题: {question}"},
        # 例: "问题: 特斯拉2025年的社会责任评分如何?"
    ]

    # 📞 调用LLM进行分类
    # temperature=0.1 表示"几乎完全确定"（不要有创意，直接给出分类）
    # 返回值例: "Route: esg_analysis"
    response = chat(messages, temperature=0.1)

    # 📝 解析LLM的回复
    choice = response.strip()  # 去掉多余的空格
    # 例: "Route: esg_analysis"

    next_node = choice.split(":")[1].strip()
    # 用":"分割: ["Route", " esg_analysis"]
    # 取第二部分并去掉空格: "esg_analysis"

    # ✅ 返回更新后的state，加入路由信息
    # 下一个Agent会收到这个结果，知道该选择哪个分支处理
    return {**state, "route": next_node}
    # 返回的新state例:
    # {
    #     "question": "分析特斯拉的ESG表现",
    #     "session_id": "xxx",
    #     "route": "esg_analysis"  # ← 新增字段
    # }


【示例2】如何理解Analyst Agent使用ESGScorer的流程

// 对标版本：在analyst_agent.py中如何调用esg_scorer

def run_analyst_with_scoring(state: dict) -> dict:
    # ① 获取检索到的上下文（来自Retriever Agent）
    context = state.get("context", "")
    # context例: "特斯拉2025年碳排放同比下降30%..."

    # ② 获取数据源管理器和评分器
    data_mgr = DataSourceManager()
    scorer = ESGScoringFramework()

    # ③ 拉取该公司的多源数据
    company_data = data_mgr.fetch_company_data(
        company_name="Tesla",
        ticker="TSLA"
    )
    # company_data 包含:
    # {
    #     "financial": {...},           # 财务数据（从Alpha Vantage）
    #     "environmental": {...},       # 环保数据（从Hyfinnan）
    #     "social": {...},              # 社会数据（从新闻API）
    #     "governance": {...},          # 治理数据（从SEC EDGAR）
    #     "recent_news": [...]          # 最新新闻
    # }

    # ④ 使用ESGScorer进行15维度评分
    esg_report = scorer.score_esg(
        company_name="Tesla",
        esg_data=company_data.dict()
    )
    # esg_report 包含:
    # {
    #     "overall_score": 78.5,
    #     "e_scores": {                 # 环境维度
    #         "carbon_emissions": 82,
    #         "energy_efficiency": 75,
    #         ...
    #     },
    #     "s_scores": {...},            # 社会维度
    #     "g_scores": {...},            # 治理维度
    #     "key_strengths": [...],       # 优势
    #     "key_weaknesses": [...]       # 劣势
    # }

    # ⑤ 生成可视化数据（给前端展示）
    visualizer = ESGVisualizer()
    charts = visualizer.generate_report_visual(esg_report)
    # charts 包含:
    # {
    #     "radar": {...},       # 雷达图数据
    #     "bars": {...},        # 柱状图数据
    #     "heatmap": {...},     # 热力图数据
    #     "gauges": {...},      # 仪表盘数据
    #     ...
    # }

    # ⑥ 返回完整的分析结果
    return {
        **state,
        "esg_scores": esg_report.dict(),
        "visualizations": charts,
        "analysis_summary": f"特斯拉综合评分: {esg_report.overall_score}"
    }


================================================================================
第五部分：问题检查与修正清单
================================================================================

【✅ 已确认正常的设计】

1. ✅ 模块化架构
   • 每个模块职责单一，易于维护和扩展
   • 符合SOLID原则

2. ✅ 错误处理和降级
   • LLM Fallback链: Claude → GPT-4 → DeepSeek → 本地模型
   • 数据源异常时有默认值
   • 日志完整，便于故障排查

3. ✅ 缓存机制
   • RAG查询结果缓存6小时
   • 数据源查询结果缓存24小时
   • 防止重复调用和浪费API配额

4. ✅ 数据库事务
   • 推送通知有幂等性（同一条通知不会发送两次）
   • 重要操作有日志记录


【⚠️ 需要注意的潜在问题和改进】

1. 【问题】API Rate Limiting
   现象: 如果同时请求太多ESG评分，可能触发LLM API限流

   当前处理: 有重试机制 + 指数退避
   改进建议:
     • 添加请求队列，限制并发数
     • 实现优先级队列 (VIP用户优先)
     • 预热缓存 (定期更新热门公司数据)

   代码位置: gateway/utils/retry.py

2. 【问题】数据不一致性
   现象: 不同数据源可能给出矛盾的数据
   例: Alpha Vantage说特斯拉市值500B，Finnhub说480B

   当前处理: 无
   改进建议:
     • 添加数据一致性验证逻辑
     • 为不同来源分配可信度权重
     • 当数据差异超过阈值时告警

   代码示例:
     def validate_data_consistency(data_sources):
         # 比较不同来源的市值
         mv_alpha = data_sources["alpha_vantage"]["market_cap"]
         mv_finnhub = data_sources["finnhub"]["market_cap"]

         diff_percent = abs(mv_alpha - mv_finnhub) / mv_alpha * 100

         if diff_percent > 10:  # 超过10%差异
             logger.warning(f"数据不一致: {diff_percent}%的差异")
             # 选择可信度更高的数据源的值
             return max(mv_alpha, mv_finnhub, key=data_sources.trust_score)

3. 【问题】报告生成延迟
   现象: 报告生成需要30-60秒，可能超时

   当前处理: 使用异步任务 (background_tasks)
   改进建议:
     • 使用专业的任务队列 (Celery + Redis)
     • 分阶段生成 (先生成核心内容，后补充图表)
     • 流式返回 (边生成边返回给用户)

   代码位置: gateway/scheduler/report_scheduler.py

4. 【问题】推送规则的安全性
   现象: PushRule使用eval()执行用户输入的条件表达式

   当前代码:
     if eval(rule.condition, {"__builtins__": {}}, context):
     # 这有代码注入风险!

   改进建议:
     • 使用安全的表达式评估库 (simpleeval)
     • 预定义条件的白名单
     • 验证规则条件的安全性

   改进代码:
     from simpleeval import simple_eval

     # 定义允许的字段和操作符
     ALLOWED_VARS = ["esg_score", "risk_level", "company_count"]
     ALLOWED_OPS = ["<", ">", "==", "and", "or"]

     try:
         result = simple_eval(rule.condition, names=context)
     except Exception as e:
         logger.error(f"条件表达式错误: {e}")
         result = False

5. 【问题】性能瓶颈识别

   a) LLM调用最慢
      • 解决: 缓存常见问题的答案
      • 预计改进: 速度提升3-5倍

   b) 数据库查询
      • 解决: 添加更多索引
      • 预计改进: 速度提升2-3倍

   c) 向量搜索
      • 当前: FAISS (本地)
      • 改进: 迁移到Pinecone (云端) 以支持更大规模

   性能测试代码:
     import time

     def profile_esg_score(company_name):
         start = time.time()
         result = scorer.score_esg(company_name)
         elapsed = time.time() - start

         print(f"总耗时: {elapsed:.2f}秒")
         print(f"  - 数据拉取: {elapsed*0.3:.2f}秒")
         print(f"  - LLM评分: {elapsed*0.6:.2f}秒")
         print(f"  - 可视化: {elapsed*0.1:.2f}秒")


【🔧 代码质量改进建议】

1. 添加类型注解覆盖
   当前: 70% 的函数有完整类型注解
   目标: 100% 的函数有完整类型注解

   示例:
     # ❌ 不好
     def fetch_data(company):
         ...

     # ✅ 好
     def fetch_data(company: str) -> Dict[str, Any]:
         ...

2. 添加单元测试
   当前: 仅有集成测试 (demo_scheduler.py, test_scheduler.py)
   缺失: 单元测试，测试覆盖率 < 30%

   需要添加:
     • tests/test_esg_scorer.py         (测试评分逻辑)
     • tests/test_data_sources.py       (测试数据融合)
     • tests/test_push_rules.py         (测试推送规则)

   例子:
     def test_esg_scorer_15_dimensions():
         """验证评分器能正确计算15个维度"""
         scorer = ESGScoringFramework()
         report = scorer.score_esg("Tesla", mock_data)

         # 验证E维度有5个指标
         assert len(report.e_scores.metrics) == 5
         # 验证评分在0-100之间
         assert 0 <= report.overall_score <= 100
         # 验证权重和为1
         assert sum(m.weight for m in report.e_scores.metrics.values()) == 1.0

3. 文档更新
   当前: 代码注释较少
   改进: 添加docstring和使用示例

   例子:
     def score_esg(self, company_name: str, esg_data: Dict[str, Any]) -> ESGScoreReport:
         """
         对公司进行15维度ESG评分。

         Args:
             company_name: 公司名称 (e.g., "Tesla")
             esg_data: 多源汇总的ESG数据 (来自DataSourceManager)

         Returns:
             ESGScoreReport: 包含15个指标的完整评分报告

         Example:
             >>> data_mgr = DataSourceManager()
             >>> company_data = data_mgr.fetch_company_data("Tesla", "TSLA")
             >>> scorer = ESGScoringFramework()
             >>> report = scorer.score_esg("Tesla", company_data.dict())
             >>> print(f"总分: {report.overall_score}")
             总分: 78.5
         """


================================================================================
第六部分：前端美化与演示方案
================================================================================

【当前状态】
目前没有专门的Web UI，所有交互都是通过API。
演示方式: Postman、curl命令或SDK调用

【推荐的前端方案】

方案1: Web Dashboard (推荐，最专业)
────────────────────────────────

技术栈:
  • 框架: React 18 + TypeScript
  • UI库: TailwindCSS + Shadcn/ui (美观专业)
  • 图表: Recharts (数据可视化)
  • 状态管理: Zustand
  • API客户端: TanStack Query (React Query)

核心功能:
  1. ESG评分仪表板
     ✨ 展示E/S/G三维雷达图
     ✨ 可拖拽的小部件 (Draggable Widgets)
     ✨ 实时数据更新

  2. 深度分析页面
     ✨ 15个指标的详细柱状图
     ✨ 与行业对标的热力图
     ✨ 时间序列趋势分析

  3. 报告管理面板
     ✨ 日/周/月报告的生成历史
     ✨ 报告下载 (PDF/Excel)
     ✨ 报告分享链接生成

  4. 推送规则编辑器
     ✨ 可视化规则构建器
     ✨ 规则预览和测试
     ✨ 推送历史和效果分析

前端项目结构:
  frontend/
  ├─ src/
  │  ├─ pages/
  │  │  ├─ Dashboard.tsx        ESG评分主仪表板
  │  │  ├─ AnalysisDetail.tsx   15维度详细分析
  │  │  ├─ Reports.tsx          报告管理
  │  │  └─ PushRules.tsx        推送规则编辑
  │  ├─ components/
  │  │  ├─ Charts/
  │  │  │  ├─ RadarChart.tsx    雷达图
  │  │  │  ├─ BarChart.tsx      柱状图
  │  │  │  └─ Heatmap.tsx       热力图
  │  │  └─ Layout/
  │  │     ├─ Header.tsx        导航栏
  │  │     └─ Sidebar.tsx       侧边栏
  │  └─ api/
  │     └─ client.ts            API客户端
  └─ package.json

前端截图设想:

  【主仪表板】
  ┌─────────────────────────────────────────────────┐
  │  ESG Agentic RAG Copilot                  🌙    │
  ├─────────────────────────────────────────────────┤
  │                                                 │
  │  公司: [Tesla 🔍]  日期: 2026-03-29  [刷新]    │
  │                                                 │
  │  ┌──────────────┐  ┌──────────────┐           │
  │  │ 综合ESG评分  │  │ 行业排名      │           │
  │  │     78.5     │  │   Top 15%    │           │
  │  │   良好 ⭐⭐⭐⭐  │              │           │
  │  └──────────────┘  └──────────────┘           │
  │                                                 │
  │        ╱──────\    ↑ 环境 (85)                  │
  │       │    85  │  /  \                        │
  │       │ 环  治 │ /    \                       │
  │       │ 85 75  70  社  70                    │
  │        \────────/                             │
  │                                                 │
  │  核心优势:                 改进方向:           │
  │  ✓ 可再生能源 92          ⚠ 员工薪酬 55       │
  │  ✓ 董事会多样性 88        ⚠ 水资源管理 65     │
  │  ✓ 反腐机制 90           ⚠ 供应链伦理 60     │
  │                                                 │
  └─────────────────────────────────────────────────┘


方案2: 移动应用 (次选)
────────────────────────

技术: React Native 或 Flutter
优点: 随时随地查看ESG评分
缺点: 图表展示受限


方案3: 命令行界面 (CLI) (学习用)
────────────────────────────

技术: Click (Python) 或 Typer
优点: 快速、无依赖
缺点: 交互体验不如Web


【推荐方案】: 方案1 (React Web Dashboard)

实现步骤:
  1. 创建React项目 (使用 create-vite)
  2. 安装依赖 (TailwindCSS, Recharts等)
  3. 实现4个主要页面
  4. 连接后端API
  5. 部署到Vercel或Netlify

预计工作量: 2-3周 (一人)


================================================================================
第七部分：下一步优化方向 - 从Single-Agent到Multi-Agent
================================================================================

【当前架构分析】

当前是什么:
  ✓ Single Agent Workflow (单一LLM链)
    Router → Retriever → Analyst → Verifier

  ✓ 定时任务系统 (但只有1个Agent)
    Scanner → Extractor → Scorer → Matcher → Notifier

  ✗ 不是Multi-Agent: 没有多个独立的Agent相互协作


【为什么需要Multi-Agent】

当前系统的痛点:
  1. Agent职责不够独立，容易相互影响
  2. 没有优先级机制 (重要任务可能被平凡任务卡住)
  3. 无法并行处理 (Agent们是串行的)
  4. 难以应对复杂问题 (需要多个Agent的专业分工)

Multi-Agent的优势:
  • 并行计算: 多个Agent同时工作，速度更快
  • 专业分工: 每个Agent只做自己擅长的事
  • 容错能力: 一个Agent失败不影响整体
  • 协作学习: Agent可以相互学习和改进


【升级路线图】

Stage 1: 当前状态 (已完成)
────────────────────────
  • Single-Agent 工作流
  • 功能: 问题回答 + 报告生成 + 推送通知
  • 架构: 串行处理


Stage 2: 引入 Multi-Agent 框架 (1-2周)
──────────────────────────────────────
  添加以下独立Agent:

  【Agent 1】Router Agent (现有，优化)
    职责: 问题分类
    输入: 用户问题
    输出: 问题类型标签

  【Agent 2】Retriever Agent (现有，优化)
    职责: 信息检索
    输入: 问题和标签
    输出: 检索到的相关文档

  【Agent 3】✨【新增】Domain Expert Agent
    职责: ESG领域专家分析
    功能:
      • 解释ESG概念
      • 给出专业建议
      • 解答深层问题

    代码框架:
      class DomainExpertAgent(BaseAgent):
          name = "domain_expert"
          description = "ESG领域专家，解答专业问题"

          def process(self, context: dict) -> dict:
              question = context["question"]
              documents = context["documents"]

              # 使用更深层的ESG知识库
              esg_knowledge = self.esg_knowledge_base.search(question)

              # 生成专业分析
              response = self.llm.call(
                  system="你是ESG领域的资深顾问...",
                  user=f"问题: {question}
相关文献: {esg_knowledge}"
              )

              return {"expert_analysis": response}

  【Agent 4】✨【新增】Risk Analyst Agent
    职责: 风险评估
    功能:
      • 识别企业风险
      • 评估风险等级
      • 建议应对措施

    代码框架:
      class RiskAnalystAgent(BaseAgent):
          name = "risk_analyst"
          description = "企业风险分析专家"

          def process(self, context: dict) -> dict:
              company = context["company"]
              financial_data = context["financial"]
              news = context["news"]

              risks = []

              # 财务风险分析
              if financial_data["debt_ratio"] > 0.6:
                  risks.append({
                      "type": "financial",
                      "level": "high",
                      "description": "债务比例过高"
                  })

              # 声誉风险分析
              negative_news = [n for n in news if n["sentiment"] < 0]
              if len(negative_news) > 5:
                  risks.append({
                      "type": "reputation",
                      "level": "medium",
                      "description": f"近期负面新闻{len(negative_news)}条"
                  })

              return {"risks": risks}

  【Agent 5】✨【新增】Recommendation Agent
    职责: 给出建议
    功能:
      • 综合各Agent的结果
      • 给出投资建议
      • 列出改进建议

    代码框架:
      class RecommendationAgent(BaseAgent):
          name = "recommender"
          description = "综合分析，给出投资和改进建议"

          def process(self, context: dict) -> dict:
              esg_score = context["esg_score"]
              risks = context["risks"]
              expert_analysis = context["expert_analysis"]
              financial = context["financial"]

              # 综合评估
              if esg_score >= 75 and len(risks) == 0:
                  recommendation = "强烈推荐"
              elif esg_score >= 60:
                  recommendation = "可以考虑"
              else:
                  recommendation = "不推荐"

              return {
                  "recommendation": recommendation,
                  "reasons": [
                      f"ESG评分: {esg_score}",
                      f"识别风险: {len(risks)}个",
                      ...
                  ]
              }


Stage 3: Agent 间的合作与学习 (2-3周)
─────────────────────────────────────

  新增能力1: Message Passing (Agent间通信)
    • Agent可以相互请求帮助
    • 例: Analyst Agent请求Domain Expert Agent解释某个概念

    代码:
      class Agent:
          def ask_other_agent(self, agent_name: str, question: str):
              target_agent = self.agent_manager.get(agent_name)
              response = target_agent.process({"question": question})
              return response

  新增能力2: Belief Sharing (信念共享)
    • Agent可以共享自己的分析结果和信心度
    • 其他Agent可以基于这些信息做决策

    代码:
      class Agent:
          def __init__(self):
              self.beliefs = {}  # 存储对各种事实的信心度

          def update_belief(self, fact: str, confidence: float):
              self.beliefs[fact] = confidence

          def get_belief(self, fact: str) -> float:
              return self.beliefs.get(fact, 0.5)  # 默认信心度50%


Stage 4: 自适应和学习 (3-4周)
──────────────────────────────

  新增能力1: Feedback Loop (反馈循环)
    记录每个Agent的预测结果，与实际结果对比

    代码:
      class FeedbackCollector:
          def record_prediction(self, agent_name, prediction, actual_result):
              # 保存记录
              self.db.insert({
                  "agent": agent_name,
                  "prediction": prediction,
                  "actual": actual_result,
                  "correct": prediction == actual_result,
                  "timestamp": datetime.now()
              })

          def get_agent_accuracy(self, agent_name, window_days=30):
              recent = self.db.query(
                  agent=agent_name,
                  timestamp__gte=datetime.now() - timedelta(days=window_days)
              )
              accuracy = sum(r["correct"] for r in recent) / len(recent)
              return accuracy

  新增能力2: Agent Tuning (Agent调优)
    根据反馈，自动调整Agent的参数

    代码:
      class AgentOptimizer:
          def optimize_agent(self, agent_name: str):
              accuracy = self.feedback.get_agent_accuracy(agent_name)

              if accuracy < 0.5:
                  # 精度太低，降低温度 (更保守)
                  agent.temperature = max(0.1, agent.temperature - 0.1)
              elif accuracy > 0.9:
                  # 精度很高，可以尝试更创意的回答
                  agent.temperature = min(0.9, agent.temperature + 0.1)


【Multi-Agent 架构图】

                      User Request
                            ↓
                    ┌─────────────────┐
                    │  Orchestrator   │ ← 中央协调器，决定调用哪个Agent
                    └────┬─┬──┬──┬────┘
                         │ │  │  └──────────────┬──────────────┐
                    ┌────▼─▼──▼──┐         ┌────▼────┐     ┌───▼───┐
                    │ Router Agent│         │ Risk    │     │ Domain│
                    │ (分类)      │         │Analyst  │     │Expert │
                    └──────┬──────┘         │(风险)   │     │(知识) │
                           │               └────┬────┘     └───┬───┘
                    ┌──────▼──────┐             │             │
                    │ Retriever   │             │             │
                    │ (检索)      │             │             │
                    └──────┬──────┘             │             │
                           │                   │             │
                    ┌──────▼───────────────────▼─────────────▼────┐
                    │         Message Queue & Belief Store         │
                    │    (Agent间通信和信息共享)                    │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │  Recommendation Agent              │
                    │  (综合分析，给出建议)               │
                    └──────────────────┬──────────────────┘
                                       │
                                       ↓
                                    Response


【Multi-Agent 的协作例子】

场景: 用户问"我应该投资特斯拉吗?"

流程:
  1. Orchestrator 识别这是一个复杂问题，需要多个Agent协作

  2. Router Agent 分类: "投资建议" → 需要多个Agent

  3. Retriever Agent 搜索特斯拉的信息

  4. Risk Analyst Agent 分析风险:
     "最近3个月有5条负面新闻关于员工纠纷，债务比例65%"

  5. Domain Expert Agent 解释:
     "特斯拉的债务比例在汽车行业属于中等，但新能源企业普遍债务较高"

  6. ESG Scorer Agent 评分:
     "综合评分78.5/100，优于行业平均"

  7. Recommendation Agent 综合所有Agent的结果:
     答案: "可以考虑，但需要关注员工关系的改善"

  对比: 单Agent只能给出肤浅的答案


【实现优先级】

优先级1 (立即做): 强烈推荐
  ✓ 代码重构:
    - 将Agent都改为继承BaseAgent类
    - 统一消息格式
    - 添加Agent注册表

优先级2 (1个月内): 推荐
  ✓ Message Queue:
    - Agent间通信
    - 数据共享

  ✓ Belief System:
    - 记录Agent的信心度
    - 用于决策

优先级3 (2-3个月): 可选
  ✓ Feedback Loop:
    - 记录预测准确率
    - 自动调优Agent参数

  ✓ Agent Learning:
    - 从反馈中学习
    - 改进策略


================================================================================
第八部分：完整的理解清单
================================================================================

如果你能回答以下问题，说明你已经掌握了这个项目:

【理解等级1: 基础认知】

□ 能解释"ESG"是什么意思，以及为什么重要？
  答: Environmental(环保)、Social(社会)、Governance(治理)
  重要性: 评估企业的可持续性和风险

□ 能说出这个项目的2大工作模式是什么？
  答: 被动分析(用户查询) 和 主动分析(定时推送)

□ 能指出项目中最重要的3个模块是什么？
  答: LangGraph (Agent工作流)、Orchestrator (调度)、ESGScorer (评分)

□ 能解释"RAG"是什么？
  答: Retrieval-Augmented Generation, 从知识库检索信息，增强LLM的准确性


【理解等级2: 中级认知】

□ 能画出完整的Agent工作流图 (Router → Retriever → Analyst → Verifier)

□ 能解释Orchestrator的5阶段流程 (Scanner → Extractor → Scorer → Matcher → Notifier)

□ 能说明15维度ESG评分体系
  - 5个E维度指标
  - 5个S维度指标
  - 5个G维度指标
  - 如何计算权重

□ 能解释DataSourceManager如何从5个来源融合数据
  - Alpha Vantage: 股价、财务
  - Hyfinnan/Yahoo Finance: ESG评级
  - SEC EDGAR: 官方披露
  - NewsAPI: 新闻
  - Finnhub: 企业信息

□ 能解释缓存和Fallback机制的作用


【理解等级3: 高级认知 - 代码理解】

□ 能读懂graph.py中的Agent编排逻辑

□ 能解释analyst_agent.py如何与esg_scorer.py协作

□ 能解释report_scheduler.py中的推送规则引擎

□ 能指出当前系统的性能瓶颈在哪里

□ 能提出至少3个代码改进建议


【理解等级4: 掌握级 - 能做事】

□ 能修改prompts.py中的提示词，改进Agent的回答质量

□ 能添加一个新的数据源到DataSourceManager

□ 能创建一个新的PushRule，实现特定的推送逻辑

□ 能调试一个报告生成失败的问题

□ 能部署整个系统到生产环境

□ 能升级系统到Multi-Agent架构


================================================================================
总结
================================================================================

这个项目的核心价值:
  ✨ 从"模糊的ESG评分" → "结构化的15维度评分"
  ✨ 从"被动回答问题" → "主动分析和推送"
  ✨ 从"单一数据源" → "5源融合"
  ✨ 从"简单通知" → "智能推送规则"

下一步的发展方向:
  🚀 升级到Multi-Agent架构
  🚀 添加更多领域专家Agent
  🚀 实现Agent的自学习和自优化
  🚀 构建web UI让非技术人员也能使用

你现在的任务:
  1. 理解这个文档 (你在做)
  2. 理解每个Python文件的代码
  3. 尝试修改和扩展功能
  4. 逐步从"Claude生成的代码" → "我的代码"

加油! 🚀
