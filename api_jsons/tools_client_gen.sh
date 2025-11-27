python ../tools/generate_types_from_api_json.py tools_all_apis.json \
    --output ../agentkit/tools/types.py \
    --base-class-name ToolsBaseModel \
    --client-output ../agentkit/tools/client.py \
    --client-class-name AgentkitToolsClient \
    --client-description "AgentKit Tools Management Service" \
    --service-name tools \
    --types-module agentkit.tools.types \
    --base-class-import agentkit.client \
    --base-client-class BaseAgentkitClient