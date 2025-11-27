python ../tools/generate_types_from_api_json.py memory_all_apis.json \
    --output ../agentkit/memory/types.py \
    --base-class-name MemoryBaseModel \
    --client-output ../agentkit/memory/client.py \
    --client-class-name AgentkitMemoryClient \
    --client-description "AgentKit Memory Management Service" \
    --service-name memory \
    --types-module agentkit.memory.types \
    --base-class-import agentkit.client \
    --base-client-class BaseAgentkitClient