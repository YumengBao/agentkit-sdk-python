python ../tools/generate_types_from_api_json.py mcp_all_apis.json \
    --output ../agentkit/mcp/types.py \
    --base-class-name MCPBaseModel \
    --client-output ../agentkit/mcp/client.py \
    --client-class-name AgentkitMCPClient \
    --client-description "AgentKit MCP (Model Context Protocol) Management Service" \
    --service-name mcp \
    --types-module agentkit.mcp.types \
    --base-class-import agentkit.client \
    --base-client-class BaseAgentkitClient