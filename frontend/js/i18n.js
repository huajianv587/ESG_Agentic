const STORAGE_KEY = 'esg_ui_locale';
const DEFAULT_LOCALE = 'zh';
const SUPPORTED_LOCALES = new Set(['zh', 'en']);
const TRANSLATABLE_ATTRIBUTES = [
  'placeholder',
  'title',
  'aria-label',
  'data-prompt',
  'data-recent-query',
];

const textOriginals = new WeakMap();
const attributeOriginals = new WeakMap();

let currentLocale = resolveInitialLocale();
let observer = null;
let isApplying = false;
let pendingApply = false;

const DOCUMENT_TITLES = {
  zh: 'ESG Agentic RAG Copilot - 企业 ESG 分析平台',
  en: 'ESG Agentic RAG Copilot - Enterprise ESG Intelligence Platform',
};

const REPLACEMENTS = [
  ['企业 ESG 分析平台', 'Enterprise ESG Intelligence Platform'],
  ['报告中心', 'Report Center'],
  ['沉浸式查看最新 ESG 情报与全部能力入口', 'An immersive view of the latest ESG intelligence and every major workflow entry point'],
  ['与 AI 对话，分析企业 ESG 表现', 'Chat with AI to analyze enterprise ESG performance'],
  ['详细评分仪表盘和可视化', 'Detailed scoring dashboard and visual analytics'],
  ['查看和管理 ESG 报告', 'View and manage ESG reports'],
  ['管理数据源和同步', 'Manage data sources and synchronization'],
  ['配置推送通知规则', 'Configure push notification rules'],
  ['管理报告订阅', 'Manage report subscriptions'],
  ['用自然语言快速进入企业 ESG 分析、问答和洞察提炼。', 'Use natural language to enter enterprise ESG analysis, Q&A, and insight generation fast.'],
  ['生成结构化评分、维度拆解和可视化，适合深度研判。', 'Generate structured scores, dimension breakdowns, and visualizations for deeper assessment.'],
  ['集中查看日报、周报和月报，把观察升级成正式输出。', 'Review daily, weekly, and monthly reports in one place and turn observations into formal outputs.'],
  ['管理数据源刷新、调度节奏和底层采集链路健康度。', 'Manage data source refreshes, scheduling cadence, and ingestion health.'],
  ['配置预警策略，把高风险 ESG 事件主动送到决策面前。', 'Configure alert strategies and proactively deliver high-risk ESG events to decision-makers.'],
  ['针对重点公司建立长期跟踪机制，持续追踪关键变化。', 'Build long-term tracking for priority companies and follow key changes continuously.'],
  ['围绕企业环境、社会与治理表现发问，快速得到分析、结论与评分摘要。', 'Ask about a company’s environmental, social, and governance performance and get quick analysis, conclusions, and score highlights.'],
  ['支持连续提问与会话历史恢复', 'Supports follow-up questions and session history restore'],
  ['输入问题，或从最近搜索继续', 'Enter a question or continue from a recent search'],
  ['把热门问题、复用查询和当前输入区组合成一个更像智能工作台的对话入口。', 'Combine hot prompts, reusable queries, and live input into a conversation workspace that feels like an analyst cockpit.'],
  ['特斯拉的环保政策评分是多少？', 'What is Tesla’s environmental policy score?'],
  ['苹果与微软的社会责任表现如何对比？', 'How do Apple and Microsoft compare on social responsibility?'],
  ['苹果与微软的社会责任对标分析', 'Compare Apple and Microsoft on social responsibility'],
  ['最近 ESG 相关风险事件有哪些？', 'What are the latest ESG-related risk events?'],
  ['微软最新的多样性报告释放了什么信号？', 'What signals come from Microsoft’s latest diversity report?'],
  ['SEC 披露规则变化会影响哪些公司？', 'Which companies could be affected by SEC disclosure rule changes?'],
  ['这里会显示你最近发起过的 ESG 对话和评分请求。', 'Your recent ESG chats and score requests will appear here.'],
  ['开始对话，分析企业ESG表现', 'Start a conversation to analyze ESG performance'],
  ['例如：分析苹果的环境政策、特斯拉的社会责任...', 'For example: analyze Apple’s environmental policy or Tesla’s social responsibility...'],
  ['输入问题...（例如：分析特斯拉的ESG表现）', 'Enter a question... (for example: analyze Tesla’s ESG performance)'],
  ['例如：分析特斯拉的 ESG 表现，或输入 Apple / Microsoft', 'For example: analyze Tesla’s ESG performance, or enter Apple / Microsoft'],
  ['例如：Tesla', 'For example: Tesla'],
  ['例如：TSLA', 'For example: TSLA'],
  ['以逗号分隔，例如：Ford,GM', 'Comma separated, for example: Ford, GM'],
  ['例如：TSLA,AAPL,MSFT', 'For example: TSLA, AAPL, MSFT'],
  ['例如：Apple,Tesla,Microsoft', 'For example: Apple, Tesla, Microsoft'],
  ['按 Shift+Enter 换行，Enter 发送', 'Press Shift+Enter for a new line, Enter to send'],
  ['请输入问题', 'Please enter a question'],
  ['输入为空', 'Input required'],
  ['思考中...', 'Thinking...'],
  ['置信度警告', 'Confidence warning'],
  ['评分生成成功', 'Score generated successfully'],
  ['生成失败', 'Generation failed'],
  ['请输入公司代码', 'Please enter company tickers'],
  ['同步任务已启动', 'Sync job started'],
  ['启动失败', 'Failed to start'],
  ['同步任务完成', 'Sync job completed'],
  ['进行中...', 'In progress...'],
  ['适合批量刷新公司 ESG 数据', 'Best for refreshing ESG data for multiple companies in batch'],
  ['选择数据源并发起同步任务，跟踪执行进度与调度统计。', 'Select data sources, launch sync jobs, and track execution progress and scheduler statistics.'],
  ['推送调度器暂未就绪，当前先展示空状态，等后端服务就绪后这里会自动恢复正常。', 'The push scheduler is not ready yet. An empty state is shown for now and will recover automatically once the backend is ready.'],
  ['支持邮件、应用内和 Webhook', 'Supports email, in-app, and webhook delivery'],
  ['管理触发条件、优先级与消息渠道，快速测试规则是否生效。', 'Manage trigger conditions, priority, and delivery channels, and quickly test whether a rule works.'],
  ['集中查看日报、周报和月报，支持异步生成与导出。', 'Review daily, weekly, and monthly reports in one place, with async generation and export support.'],
  ['生成后会自动轮询刷新状态', 'Status will be refreshed automatically after generation'],
  ['选择一份报告查看详情', 'Select a report to view details'],
  ['生成新报告', 'Generate New Report'],
  ['生成报告中...', 'Generating report...'],
  ['报告已提交生成', 'Report generation submitted'],
  ['暂无报告', 'No reports yet'],
  ['报告已生成', 'Report generated'],
  ['开始下载', 'Download started'],
  ['ESG 评分仪表盘', 'ESG Score Dashboard'],
  ['输入企业名称后生成综合评分、三维拆解和关键指标明细。', 'Enter a company name to generate an overall score, three-dimension breakdown, and key metric details.'],
  ['支持对标企业和历史数据分析', 'Supports peer comparison and historical analysis'],
  ['查询企业ESG评分', 'Query Company ESG Score'],
  ['公司名称', 'Company Name'],
  ['股票代码 (可选)', 'Ticker (Optional)'],
  ['对标公司 (可选)', 'Peer Companies (Optional)'],
  ['生成评分', 'Generate Score'],
  ['包含历史数据', 'Include Historical Data'],
  ['分析中... (这可能需要 10-30 秒)', 'Analyzing... (this may take 10-30 seconds)'],
  ['ESG 三维评分', 'ESG Dimension Scores'],
  ['维度详情', 'Dimension Details'],
  ['详细指标', 'Detailed Metrics'],
  ['维度', 'Dimension'],
  ['指标名称', 'Metric'],
  ['得分', 'Score'],
  ['权重', 'Weight'],
  ['趋势', 'Trend'],
  ['评级', 'Grade'],
  ['说明', 'Notes'],
  ['主要优势', 'Key Strengths'],
  ['主要劣势', 'Key Weaknesses'],
  ['改进建议', 'Recommendations'],
  ['在完整图表与明细表之前，先用一屏快速看清整体评分、置信度和三维拆解。', 'Before the full charts and tables, this panel gives a quick view of the overall score, confidence, and three-dimension breakdown.'],
  ['目标企业', 'Target Company'],
  ['ESG 评分请求', 'ESG score request'],
  ['环保 (E)', 'Environmental (E)'],
  ['社会 (S)', 'Social (S)'],
  ['治理 (G)', 'Governance (G)'],
  ['环境 (E)', 'Environmental (E)'],
  ['社会 (S)', 'Social (S)'],
  ['治理 (G)', 'Governance (G)'],
  ['订阅管理', 'Subscription Management'],
  ['为关注企业配置报告类型、推送频率与告警阈值。', 'Configure report types, delivery frequency, and alert thresholds for companies you follow.'],
  ['适合个人持续追踪 ESG 变化', 'Designed for continuous ESG tracking'],
  ['新建订阅', 'New Subscription'],
  ['关注的公司 (逗号分隔或标签输入)', 'Companies to follow (comma separated)'],
  ['报告类型', 'Report Types'],
  ['推送渠道', 'Delivery Channels'],
  ['推送频率', 'Delivery Frequency'],
  ['告警阈值 (可选)', 'Alert Thresholds (Optional)'],
  ['最低分数', 'Minimum Score'],
  ['最大下跌幅度', 'Maximum Drop'],
  ['创建订阅', 'Create Subscription'],
  ['我的订阅', 'My Subscriptions'],
  ['请输入至少一个公司', 'Please enter at least one company'],
  ['请选择至少一个报告类型', 'Please select at least one report type'],
  ['请选择至少一个推送渠道', 'Please select at least one delivery channel'],
  ['订阅已创建', 'Subscription created'],
  ['暂无订阅', 'No subscriptions yet'],
  ['关注公司', 'Tracked Companies'],
  ['推送渠道', 'Delivery Channels'],
  ['告警阈值', 'Alert Thresholds'],
  ['删除', 'Delete'],
  ['编辑', 'Edit'],
  ['编辑功能开发中', 'Edit flow is under development'],
  ['订阅于', 'Subscribed on'],
  ['推送规则', 'Push Rules'],
  ['规则名称', 'Rule Name'],
  ['条件表达式', 'Condition Expression'],
  ['目标用户', 'Target Users'],
  ['所有用户', 'All Users'],
  ['股东', 'Shareholders'],
  ['追踪者', 'Followers'],
  ['分析师', 'Analysts'],
  ['优先级 (1-10)', 'Priority (1-10)'],
  ['通知模板', 'Notification Template'],
  ['低分预警', 'Low Score Alert'],
  ['优秀案例', 'Best Practice'],
  ['关键风险', 'Critical Risk'],
  ['每日摘要', 'Daily Digest'],
  ['已更新', 'Updated'],
  ['更新失败', 'Update failed'],
  ['测试失败', 'Test failed'],
  ['确认删除', 'Confirm Delete'],
  ['确定要删除此规则吗？', 'Are you sure you want to delete this rule?'],
  ['已删除', 'Deleted'],
  ['删除失败', 'Delete failed'],
  ['编辑规则', 'Edit Rule'],
  ['新建规则', 'New Rule'],
  ['规则已更新', 'Rule updated'],
  ['规则已创建', 'Rule created'],
  ['保存失败', 'Save failed'],
  ['日报', 'Daily'],
  ['周报', 'Weekly'],
  ['月报', 'Monthly'],
  ['包含对标分析', 'Include peer comparison'],
  ['执行摘要', 'Executive Summary'],
  ['关键发现', 'Key Findings'],
  ['企业分析', 'Company Analysis'],
  ['暂无摘要', 'No summary available'],
  ['排名:', 'Rank:'],
  ['导出 PDF', 'Export PDF'],
  ['导出 Excel', 'Export Excel'],
  ['数据同步', 'Data Sync'],
  ['选择数据源', 'Select Data Sources'],
  ['公司代码或名称 (逗号分隔)', 'Company Tickers or Names (Comma Separated)'],
  ['强制刷新缓存', 'Force Refresh Cache'],
  ['开始同步', 'Start Sync'],
  ['进行中的任务', 'Active Jobs'],
  ['调度统计', 'Scheduler Stats'],
  ['进度', 'Progress'],
  ['个错误', 'errors'],
  ['调度器当前未完全就绪，以下统计为占位数据。基础页面可正常使用，相关后台任务可稍后再试。', 'The scheduler is not fully ready yet. The statistics below are placeholders, while the core page remains usable.'],
  ['总扫描次数', 'Total Scans'],
  ['成功率', 'Success Rate'],
  ['最后同步', 'Last Sync'],
  ['未同步', 'Not Synced'],
  ['旗舰总览', 'Flagship Overview'],
  ['ESG 智能中枢。', 'ESG Intelligence Hub.'],
  ['ESG 智能中枢', 'ESG Intelligence Hub'],
  ['把最近 ESG 情报做成一套旗舰级的信息体验。', 'Turn recent ESG intelligence into a flagship-grade information experience.'],
  ['在一个总览页面中掌握最新 ESG 动态与关键操作入口。', 'Use a single overview page to track the latest ESG activity and core action points.'],
  ['智能查询界面', 'Intelligent Query Interface'],
  ['智能搜索', 'Smart Search'],
  ['请输入公司名称或 ESG 相关问题', 'Enter a company name or an ESG-related question'],
  ['进入 ESG 对话', 'Open ESG Chat'],
  ['打开评分看板', 'Open Score Dashboard'],
  ['热门问题', 'Hot Questions'],
  ['评分看板', 'Score Dashboard'],
  ['实时问答', 'Real-time Q&A'],
  ['结构评分', 'Structured Scoring'],
  ['周期报告', 'Recurring Reports'],
  ['数据底座', 'Data Foundation'],
  ['智能触达', 'Intelligent Delivery'],
  ['持续跟踪', 'Continuous Tracking'],
  ['上次搜索', 'Recent Searches'],
  ['支持一键复用', 'One-click reuse'],
  ['ESG 评分看板', 'ESG Scoreboard'],
  ['综合评分、三维拆解、雷达图与趋势图在同一屏内形成专业驾驶舱视角。', 'Overall score, dimension breakdowns, radar views, and trends come together in one cockpit-like screen.'],
  ['ESG 事件监测', 'ESG Event Monitoring'],
  ['最近 7 天的风险事件、推荐措施和时间线视图统一编排，便于快速判断优先级。', 'The last seven days of risk events, recommended actions, and timeline context are arranged together for fast prioritization.'],
  ['最近的 ESG 信息流', 'Recent ESG Signal Stream'],
  ['以旗舰播片的方式展示最近进入系统视野的 ESG 信号。', 'Show the latest ESG signals in a flagship-style presentation rail.'],
  ['所有能力，一屏直达', 'All Capabilities, One Screen Away'],
  ['把 Apple 官网式的大卡片编排，服务于 ESG 智能工作流。', 'Use flagship-style large-card composition to showcase the ESG intelligence workflow.'],
  ['热问题', 'Hot Questions'],
  ['评分看板', 'Score Dashboard'],
  ['实时信号', 'Live Signals'],
  ['覆盖主体', 'Tracked Entities'],
  ['系统模块', 'System Modules'],
  ['近 7 天扫描', '7-Day Scans'],
  ['市场观察', 'Market Watch'],
  ['最新 ESG 事件', 'Latest ESG Event'],
  ['高风险', 'High Risk'],
  ['中风险', 'Medium Risk'],
  ['低风险', 'Low Risk'],
  ['观察中', 'Monitoring'],
  ['正面事件', 'Positive Event'],
  ['风险跟踪', 'Risk Follow-up'],
  ['最近 7 天', 'Last 7 Days'],
  ['评分趋势', 'Score Trend'],
  ['事件时间线视图', 'Event Timeline View'],
  ['打开', 'Open'],
  ['打开评分看板', 'Open Score Dashboard'],
  ['查看结构评分', 'View Structured Scoring'],
  ['环保', 'Environmental'],
  ['社会', 'Social'],
  ['治理', 'Governance'],
  ['ESG 对话', 'ESG Chat'],
  ['ESG 智能对话', 'ESG AI Chat'],
  ['ESG 评分', 'ESG Scoring'],
  ['把热门问题、复用查询和当前输入区合成一个更像智能工作台的对话入口。', 'Turn hot prompts, reusable queries, and the active input area into a conversation entry that feels like an intelligent workstation.'],
  ['把最新 ESG 情报、风险线索和执行入口收束成一个高端总览页面。', 'Bring the latest ESG intelligence, risk signals, and action entry points into one premium overview page.'],
  ['像旗舰发布页一样编排信息，第一眼看到最新脉搏，第二步进入分析与行动。', 'Arrange information like a flagship launch page: see the latest pulse first, then move straight into analysis and action.'],
  ['像旗舰发布页一样呈现 ESG 情报、评分看板、事件监测与执行入口。', 'Present ESG intelligence, scoring dashboards, event monitoring, and action entry points like a flagship launch page.'],
  ['像旗舰发布页一样呈现ESG情报、ScoreDashboard、事件监测与执行入口。', 'Present ESG intelligence, scoring dashboards, event monitoring, and action entry points like a flagship launch page.'],
  ['像旗舰发布页一样呈现 ESG 情报、ScoreDashboard、事件监测与执行入口。', 'Present ESG intelligence, scoring dashboards, event monitoring, and action entry points like a flagship launch page.'],
  ['把公司名、问题、热门话题与最近搜索收束成一个真正像旗舰产品的查询入口。', 'Bring company names, questions, hot topics, and recent searches into a query entry that feels like a flagship product.'],
  ['将 QueryInterface、ScoreBoard、EventMonitor 和功能矩阵收束成一个高端总览页面，让信息一眼可读、功能一键可达。', 'Bring Query Interface, Scoreboard, Event Monitor, and the feature matrix into one premium overview so insights are instantly readable and actions are one click away.'],
  ['将QueryInterface、ScoreBoard、EventMonitor和功能矩阵收束成一个高端总览页面，让信息一眼可读、功能一键可达。', 'Bring Query Interface, Scoreboard, Event Monitor, and the feature matrix into one premium overview so insights are instantly readable and actions are one click away.'],
  ['这里会记录你最近发起过的 ESG 查询和评分动作。', 'Your recent ESG queries and score actions will appear here.'],
  ['最新 ESG 信号已进入视野', 'The latest ESG signal is now in view'],
  ['综合评分', 'Overall Score'],
  ['维度雷达', 'Dimension Radar'],
  ['E 维度', 'E Dimension'],
  ['S 维度', 'S Dimension'],
  ['G 维度', 'G Dimension'],
  ['推荐措施：', 'Recommended Action: '],
  ['持续跟踪后续披露与执行动作。', 'Continue tracking follow-up disclosures and execution steps.'],
  ['优先补充正式回应，并排查治理与劳工风险。', 'Prioritize a formal response and review governance and labor risks.'],
  ['RAG 检索', 'RAG Retrieval'],
  ['调度器', 'Scheduler'],
  ['数据源', 'Data Sources'],
  ['碳排放', 'Carbon Emissions'],
  ['员工满意度', 'Employee Satisfaction'],
  ['供应链伦理', 'Supply Chain Ethics'],
  ['能源效率', 'Energy Efficiency'],
  ['成本竞争力', 'Cost Competitiveness'],
  ['持续观察后续披露，并加入行业对标。', 'Monitor future disclosures and add industry benchmarking.'],
  ['作为正面案例继续跟踪，提炼可复用亮点。', 'Keep tracking this positive case and distill reusable highlights.'],
  ['像旗舰发布页一样展示 ESG 情报、系统能力和核心入口。', 'Present ESG intelligence, system capabilities, and core entry points like a flagship launch page.'],
  ['让研究、监测和执行不再分散在多个页面里，而是在一个总览视角里建立秩序。', 'Bring research, monitoring, and execution into a single orderly overview instead of scattering them across multiple pages.'],
  ['Tesla 更新碳减排目标，成为当前 ESG 关注焦点。', 'Tesla updates its carbon reduction targets and becomes a focal ESG topic.'],
  ['环境目标的重新量化，通常会对供应链执行、资本市场叙事与长期治理预期同时产生影响。', 'Reframing environmental targets can simultaneously affect supply-chain execution, capital-market narratives, and long-term governance expectations.'],
  ['最近进入首页的信息流', 'Signals recently surfaced on the home view'],
  ['最近进入旗舰首页的信息流', 'Signals recently surfaced on the flagship home view'],
  ['当前热点主体数量', 'Number of entities currently in focus'],
  ['当前热点涉及的企业或监管主体', 'Companies or regulators currently in focus'],
  ['在线能力概览', 'Online capability snapshot'],
  ['当前在线的分析与调度能力', 'Analytics and orchestration capabilities currently online'],
  ['等待调度器接管', 'Waiting for scheduler takeover'],
  ['调度器扫描统计', 'Scheduler scan statistics'],
  ['员工劳资纠纷进入舆情高位', 'Labor disputes move to the top of public attention'],
  ['工人权益议题快速放大，可能影响社会责任评分和治理叙事。', 'Worker-rights issues are escalating quickly and may affect social scores and governance narratives.'],
  ['改善员工薪酬与工作条件，并补充正式披露回应。', 'Improve employee pay and working conditions, and supplement formal disclosures.'],
  ['供应链碳排放审计结果发布', 'Supply chain carbon audit results released'],
  ['供应链减排与可再生能源使用比例成为市场关注重点。', 'Supply-chain decarbonization and renewable-energy usage ratios have become a market focus.'],
  ['增加可再生能源使用比例，并强化供应链沟通。', 'Increase renewable-energy usage and strengthen supplier communication.'],
  ['多样性报告公布新的改善指标', 'Diversity report releases new improvement metrics'],
  ['正面社会责任样本出现，适合持续跟踪并用于横向对标。', 'A positive social-responsibility case has emerged and is worth tracking as a peer benchmark.'],
  ['持续观察后续披露，把亮点沉淀成对标样本。', 'Keep watching follow-up disclosures and turn the highlights into benchmark examples.'],
  ['持续跟踪披露进度并评估治理回应质量。', 'Track disclosure progress continuously and assess the quality of governance responses.'],
  ['补充行业对标并观察后续执行动作。', 'Add industry benchmarking and monitor follow-up execution.'],
  ['Tesla 宣布更激进的碳减排时间表', 'Tesla announces a more aggressive carbon reduction timeline'],
  ['环境目标的提前意味着更高的执行要求，也释放出更积极的转型信号。', 'Bringing environmental targets forward raises execution expectations and signals a more proactive transition.'],
  ['Microsoft 最新 ESG 报告强化可再生能源路线', 'Microsoft’s latest ESG report reinforces its renewable-energy roadmap'],
  ['新报告强调长期治理与能源结构调整，利于稳定市场预期。', 'The new report emphasizes long-term governance and energy-mix adjustment, helping stabilize market expectations.'],
  ['SEC 披露规则变化提升治理合规压力', 'Changes to SEC disclosure rules increase governance compliance pressure'],
  ['披露要求细化后，企业需要更系统地组织 ESG 证据链和治理响应。', 'As disclosure requirements become more detailed, companies need a more systematic ESG evidence chain and governance response.'],
  ['发送', 'Send'],
  ['条件', 'Condition'],
  ['状态', 'Status'],
  ['操作', 'Actions'],
  ['测试', 'Test'],
  ['启用', 'Enabled'],
  ['禁用', 'Disabled'],
  ['加载失败', 'Load failed'],
  ['创建失败', 'Creation failed'],
  ['验证失败', 'Validation failed'],
  ['同步中...', 'Syncing...'],
  ['公司列表 (逗号分隔)', 'Company List (Comma Separated)'],
  ['未知', 'Unknown'],
  ['确定要删除此订阅吗？', 'Are you sure you want to delete this subscription?'],
  ['-- 选择 --', '-- Select --'],
  ['页面加载失败', 'Page failed to load'],
  ['SEC 的 ESG 综合评分是多少？', 'What is SEC’s overall ESG score?'],
  ['SEC 最近有哪些 ESG 风险事件？', 'What recent ESG risk events involve the SEC?'],
  ['苹果与微软的社会责任表现如何对比？', 'How do Apple and Microsoft compare on social responsibility?'],
  ['最近 7 天有哪些值得关注的 ESG 风险信号？', 'Which ESG risk signals are worth watching over the last 7 days?'],
  ['Positive', 'Positive'],
  ['Alert', 'Alert'],
  ['Neutral', 'Neutral'],
  ['确认', 'Confirm'],
  ['取消', 'Cancel'],
  ['提示', 'Notice'],
  ['确定', 'OK'],
  ['提交', 'Submit'],
  ['表单', 'Form'],
  ['请稍候', 'Please wait'],
  ['加载中...', 'Loading...'],
  ['默认: 40', 'Default: 40'],
  ['默认: 5', 'Default: 5'],
  ['成功', 'Success'],
  ['错误', 'Error'],
  ['警告', 'Warning'],
  ['接口错误', 'API Error'],
  ['连接失败', 'Connection failed'],
  ['后端已连接', 'Backend connected'],
  ['等待后端响应', 'Waiting for backend'],
  ['检查连接中...', 'Checking connection...'],
  ['无法连接到后端服务', 'Unable to connect to the backend service'],
  ['网络已连接', 'Network connected'],
  ['网络已断开连接', 'Network disconnected'],
  ['网络错误', 'Network error'],
  ['无效日期', 'Invalid date'],
  ['刚刚', 'Just now'],
  [' 分钟前', ' minutes ago'],
  [' 小时前', ' hours ago'],
  [' 天前', ' days ago'],
  ['实时', 'Real-time'],
  ['每日', 'Daily'],
  ['每周', 'Weekly'],
  ['邮件', 'Email'],
  ['应用内', 'In-App'],
  ['应用内消息', 'In-App Message'],
  ['Webhook', 'Webhook'],
  ['Online', 'Online'],
  ['Standby', 'Standby'],
  ['请选择', 'Select'],
  ['暂无规则', 'No rules yet'],
  ['暂无报告', 'No reports yet'],
  ['暂无订阅', 'No subscriptions yet'],
  ['暂无进行中的任务', 'No active jobs'],
];

const REGEX_REPLACEMENTS = [
  [/^(.+?) 的评分总览$/u, '$1 Score Overview'],
  [/^(.+?) 的 ESG 评分$/u, '$1 ESG Score'],
  [/^ESG\s*智能中枢[。.]?$/u, 'ESG Intelligence Hub'],
  [/^置信度\s*(.+)$/u, 'Confidence $1'],
  [/^置信度较低\s*\((.+)\)，结果可能不准确$/u, 'Low confidence ($1). Results may be inaccurate'],
  [/^平均分:\s*(.+)$/u, 'Average score: $1'],
  [/^排名:\s*(.+)$/u, 'Rank: $1'],
  [/^完成:\s*(.+)$/u, 'Completed: $1'],
  [/^订阅于\s*(.+)$/u, 'Subscribed on $1'],
  [/^ESG 分数:\s*(.+)$/u, 'ESG score: $1'],
  [/^下跌幅度:\s*(.+)$/u, 'Drop threshold: $1'],
  [/^(\d+)\s*家公司$/u, '$1 companies'],
  [/^(\d+)\s*家企业$/u, '$1 companies'],
  [/^(\d+)\s*条$/u, '$1 signals'],
  [/^(\d+)\s*个$/u, '$1 entities'],
  [/^(\d+)\s*次$/u, '$1 scans'],
  [/^(\d+)\s*个错误$/u, '$1 errors'],
  [/^❌\s*错误:\s*(.+)$/u, '❌ Error: $1'],
  [/^例如：/u, 'For example: '],
  [/^默认:\s*/u, 'Default: '],
];

const SORTED_REPLACEMENTS = [...REPLACEMENTS].sort((a, b) => b[0].length - a[0].length);

function resolveInitialLocale() {
  const stored = window.__ESG_UI_LOCALE__ || window.localStorage?.getItem(STORAGE_KEY) || DEFAULT_LOCALE;
  return SUPPORTED_LOCALES.has(stored) ? stored : DEFAULT_LOCALE;
}

function shouldSkipNode(node) {
  const parent = node.parentElement;
  if (!parent) return true;
  if (parent.closest('[data-no-i18n="true"]')) return true;
  const tagName = parent.tagName;
  return tagName === 'SCRIPT' || tagName === 'STYLE';
}

function translateText(text) {
  if (typeof text !== 'string' || currentLocale !== 'en') {
    return text;
  }

  let result = text;
  for (const [from, to] of SORTED_REPLACEMENTS) {
    result = result.split(from).join(to);
  }
  for (const [pattern, replacement] of REGEX_REPLACEMENTS) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

function getOriginalAttribute(element, attr) {
  let attrMap = attributeOriginals.get(element);
  if (!attrMap) {
    attrMap = new Map();
    attributeOriginals.set(element, attrMap);
  }
  if (!attrMap.has(attr)) {
    attrMap.set(attr, element.getAttribute(attr));
  }
  return attrMap.get(attr);
}

function applyToTextNodes(root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    if (!node.nodeValue || !node.nodeValue.trim() || shouldSkipNode(node)) {
      continue;
    }
    if (!textOriginals.has(node)) {
      textOriginals.set(node, node.nodeValue);
    }
    const original = textOriginals.get(node);
    const nextValue = currentLocale === 'en' ? translateText(original) : original;
    if (node.nodeValue !== nextValue) {
      node.nodeValue = nextValue;
    }
  }
}

function applyToAttributes(root) {
  const elements = [];
  if (root.nodeType === Node.ELEMENT_NODE) {
    elements.push(root);
  }
  if (root.querySelectorAll) {
    elements.push(...root.querySelectorAll('*'));
  }

  elements.forEach((element) => {
    if (element.closest('[data-no-i18n="true"]')) {
      return;
    }
    TRANSLATABLE_ATTRIBUTES.forEach((attr) => {
      if (!element.hasAttribute(attr)) {
        return;
      }
      const original = getOriginalAttribute(element, attr);
      const nextValue = currentLocale === 'en' ? translateText(original) : original;
      if (element.getAttribute(attr) !== nextValue) {
        element.setAttribute(attr, nextValue);
      }
    });
  });
}

function updateDocumentMeta() {
  document.documentElement.lang = currentLocale === 'en' ? 'en' : 'zh-CN';
  document.title = DOCUMENT_TITLES[currentLocale] || DOCUMENT_TITLES.zh;
}

function updateToggleState() {
  const buttons = document.querySelectorAll('[data-locale]');
  buttons.forEach((button) => {
    button.classList.toggle('is-active', button.dataset.locale === currentLocale);
    button.setAttribute('aria-pressed', String(button.dataset.locale === currentLocale));
  });
}

export function getLocale() {
  return currentLocale;
}

export function setLocale(locale) {
  const nextLocale = SUPPORTED_LOCALES.has(locale) ? locale : DEFAULT_LOCALE;
  if (nextLocale === currentLocale) {
    return;
  }

  currentLocale = nextLocale;
  window.__ESG_UI_LOCALE__ = currentLocale;
  window.localStorage?.setItem(STORAGE_KEY, currentLocale);
  applyLocale(document.body);
  updateToggleState();
  window.dispatchEvent(new CustomEvent('locale-change', {
    detail: { locale: currentLocale },
  }));
}

export function applyLocale(root = document.body) {
  if (!root) return;

  isApplying = true;
  try {
    updateDocumentMeta();
    applyToAttributes(root);
    applyToTextNodes(root);
    updateToggleState();
  } finally {
    isApplying = false;
  }
}

function scheduleApply(root = document.body) {
  if (pendingApply) {
    return;
  }
  pendingApply = true;
  window.requestAnimationFrame(() => {
    pendingApply = false;
    applyLocale(root);
  });
}

function bindLanguageSwitcher() {
  const buttons = document.querySelectorAll('[data-locale]');
  buttons.forEach((button) => {
    if (button.dataset.i18nBound === 'true') {
      return;
    }
    button.dataset.i18nBound = 'true';
    button.addEventListener('click', () => {
      setLocale(button.dataset.locale || DEFAULT_LOCALE);
    });
  });
}

function startObserver() {
  if (observer || !document.body) {
    return;
  }

  observer = new MutationObserver(() => {
    if (isApplying || currentLocale !== 'en') {
      return;
    }
    scheduleApply(document.body);
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
  });
}

export function initI18n() {
  bindLanguageSwitcher();
  startObserver();
  applyLocale(document.body);
}
