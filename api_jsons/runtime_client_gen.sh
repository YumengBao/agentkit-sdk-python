
python ../tools/generate_types_from_api_json.py runtime_all_apis.json \
    --output ../agentkit/runtime/types.py \
    --base-class-name RuntimeTypeBaseModel \
    --client-output ../agentkit/runtime/client.py \
    --client-class-name AgentkitRuntimeClient \
    --client-description "AgentKit Runtime Management Service" \
    --service-name runtime \
    --types-module agentkit.runtime.types \
    --base-class-import agentkit.client \
    --base-client-class BaseAgentkitClient