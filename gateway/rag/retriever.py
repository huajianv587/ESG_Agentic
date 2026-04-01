from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.retrievers import AutoMergingRetriever, QueryFusionRetriever
from llama_index.core.retrievers.fusion_retriever import FUSION_MODES
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.retrievers.bm25 import BM25Retriever

'''
BM25召回（关键词） ┐
                   ├→ Reciprocal Rank Fusion → 父节点扩展 → Rerank → 返回
Dense召回（语义）  ┘
'''


def build_query_engine(
    index: VectorStoreIndex,
    storage_context: StorageContext,
    leaf_nodes: list,
    similarity_top_k: int = 12,
    rerank_top_n: int = 5,
) -> RetrieverQueryEngine:

    # 1. Dense retriever（语义）
    vector_retriever = index.as_retriever(similarity_top_k=similarity_top_k)

    # 2. BM25 retriever（关键词）
    bm25_retriever = BM25Retriever.from_defaults(
        nodes=leaf_nodes,
        similarity_top_k=similarity_top_k,
    )

    # 3. Reciprocal Rank Fusion
    fusion_retriever = QueryFusionRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        similarity_top_k=similarity_top_k,
        num_queries=1,           # 不生成额外查询变体，只做融合
        mode=FUSION_MODES.RECIPROCAL_RANK,
        use_async=True,
        verbose=True,
    )

    # 4. 父节点扩展（leaf 128 token → parent 512 token）
    auto_merging_retriever = AutoMergingRetriever(
        fusion_retriever,
        storage_context=storage_context,
        simple_ratio_thresh=0.4,   #leaf占某一个父 的超过占比40%，就把对应的整个父自动取出来
        verbose=True,
    )
  
    # 5. Query engine（不设相似度过滤，128-token 小 chunk 的相似度分数普遍偏低）
    query_engine = RetrieverQueryEngine(
        retriever=auto_merging_retriever,
    )

    return query_engine
