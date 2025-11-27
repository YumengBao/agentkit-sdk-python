python ../tools/generate_types_from_api_json.py knowledge_all_apis.json \
    --output ../agentkit/knowledge/types.py \
    --base-class-name KnowledgeBaseModel \
    --client-output ../agentkit/knowledge/client.py \
    --client-class-name AgentkitKnowledgeClient \
    --client-description "AgentKit Knowledge Base Management Service" \
    --service-name knowledge \
    --types-module agentkit.knowledge.types \
    --base-class-import agentkit.client \
    --base-client-class BaseAgentkitClient