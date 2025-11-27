#!/usr/bin/env python3
"""
AgentKit SDK 完整工作流示例
============================

这个示例展示了使用新的配置管理 API 的完整工作流：
1. 初始化项目
2. 使用 AgentConfig 修改配置
3. 构建和部署 Agent
4. 调用 Agent
5. 清理资源

特性：
- ✅ 使用 InitResult.load_config() 加载配置
- ✅ 使用 AgentConfig 优雅地修改配置
- ✅ 使用 AgentKitClient 管理完整生命周期
- ✅ 完整的错误处理
"""

import sys
from agentkit.toolkit.sdk import AgentKitClient

def main():
    print("=" * 70)
    print("AgentKit SDK 完整工作流示例")
    print("=" * 70)
    print()
    
    # ========== Step 1: 初始化项目 ==========
    print("📦 Step 1: 初始化项目...")
    print("-" * 70)
    
    init_result = AgentKitClient.init_project(
        project_name="demo_planning_agent",
        template="basic_stream",
        description="一个制定计划和方案的智能 Agent",
        system_prompt="你是一个指定计划和方案的 Agent，你要做的事情就是帮助用户将问题拆分，给出整体的任务分解和步骤规划。",
        model_name="deepseek-v3-1-250821",
        tools="web_search,code_runner"
    )
    
    if not init_result.success:
        print(f"❌ 项目初始化失败: {init_result.error}")
        sys.exit(1)
    
    print("✅ 项目创建成功!")
    print(f"   项目名称: {init_result.project_name}")
    print(f"   项目路径: {init_result.project_path}")
    print(f"   配置文件: {init_result.config_file}")
    print(f"   创建文件: {len(init_result.created_files)} 个")
    print()
    
    # ========== Step 2: 使用 AgentConfig 修改配置 ==========
    print("🔧 Step 2: 配置 Agent (使用 AgentConfig API)...")
    print("-" * 70)
    
    # ✅ 新方式：使用 InitResult.load_config()
    config = init_result.load_config()
    
    print("📖 当前配置:")
    print(f"   Agent 名称: {config.agent_name}")
    print(f"   启动模式: {config.launch_type}")
    print(f"   编程语言: {config.language} {config.language_version}")
    print(f"   入口文件: {config.entry_point}")
    print()
    
    # 修改配置为 local 模式（方便本地测试）
    print("🔧 修改启动模式为 local...")
    config.launch_type = "local"
    
    # 添加环境变量
    config.add_runtime_env("LOG_LEVEL", "DEBUG")
    config.add_runtime_env("ENVIRONMENT", "development")
    
    # 保存配置
    config.save()
    print("✅ 配置已更新并保存")
    print(f"   启动模式: {config.launch_type}")
    print(f"   环境变量: {len(config.runtime_envs)} 个")
    print()
    
    # ========== Step 3: 创建 Client ==========
    print("🤖 Step 3: 创建 AgentKitClient...")
    print("-" * 70)
    
    # ✅ 方式 1: 使用 AgentConfig 对象（推荐）
    client = AgentKitClient(config)
    print("✅ Client 已创建（使用 AgentConfig 对象）")
    print()
    
    # 或者使用 InitResult.create_client() 一步到位
    # client = init_result.create_client(launch_type="local")
    
    # ========== Step 4: 构建 Agent ==========
    print("🔨 Step 4: 构建 Agent 镜像...")
    print("-" * 70)
    
    build_result = client.build()
    
    if not build_result.success:
        print(f"❌ 构建失败: {build_result.error}")
        print(f"   错误类型: {build_result.error_type}")
        sys.exit(1)
    
    print("✅ 构建成功!")
    print(f"   镜像名称: {build_result.image_name}")
    print(f"   镜像 ID: {build_result.image_id}")
    print(f"   镜像标签: {build_result.image_tag}")
    print()
    
    # ========== Step 5: 部署 Agent ==========
    print("🚀 Step 5: 部署 Agent...")
    print("-" * 70)
    
    deploy_result = client.deploy()
    
    if not deploy_result.success:
        print(f"❌ 部署失败: {deploy_result.error}")
        sys.exit(1)
    
    print("✅ 部署成功!")
    print(f"   服务端点: {deploy_result.endpoint_url}")
    print(f"   容器 ID: {deploy_result.container_id}")
    print(f"   服务 ID: {deploy_result.service_id}")
    print()
    
    # ========== Step 6: 查询状态 ==========
    print("📊 Step 6: 查询 Agent 状态...")
    print("-" * 70)
    
    status_result = client.status()
    
    if status_result.success:
        print("✅ 状态查询成功!")
        print(f"   运行状态: {status_result.status.value}")
        print(f"   是否运行: {'是' if status_result.is_running() else '否'}")
        print(f"   服务端点: {status_result.endpoint_url}")
        if status_result.uptime:
            print(f"   运行时长: {status_result.uptime}")
    else:
        print(f"⚠️  状态查询失败: {status_result.error}")
    print()
    
    # ========== Step 7: 调用 Agent ==========
    print("💬 Step 7: 调用 Agent...")
    print("-" * 70)
    
    # 准备调用参数
    payload = {
        "prompt": "请帮我制定一个学习 Python 的计划，我是初学者，每天可以投入 2 小时学习。"
    }
    
    headers = {
        "user_id": "demo_user_001",
        "session_id": "demo_session_001"
    }
    
    print("📤 发送请求:")
    print(f"   提示词: {payload['prompt'][:50]}...")
    print(f"   用户 ID: {headers['user_id']}")
    print()
    
    invoke_result = client.invoke(
        payload=payload,
        headers=headers
    )
    
    if not invoke_result.success:
        print(f"❌ 调用失败: {invoke_result.error}")
        print(f"   错误类型: {invoke_result.error_type}")
    else:
        print("✅ 调用成功!")
        
        # 处理响应
        if invoke_result.is_streaming:
            print("📡 流式响应:")
            print("-" * 70)
            try:
                for event in invoke_result.stream():
                    # 打印每个事件
                    if isinstance(event, dict):
                        if 'content' in event:
                            print(event['content'], end='', flush=True)
                        elif 'data' in event:
                            print(event['data'], end='', flush=True)
                    else:
                        print(event, end='', flush=True)
                print()  # 换行
            except Exception as e:
                print(f"\n⚠️  流式响应处理出错: {e}")
        else:
            print("📥 响应:")
            print("-" * 70)
            print(invoke_result.response)
    
    print()
    print("-" * 70)
    print()
    
    # ========== Step 8: 清理资源 ==========
    print("🧹 Step 8: 清理资源...")
    print("-" * 70)
    
    cleanup = input("是否清理资源（停止并删除容器）? (y/N): ").strip().lower()
    
    if cleanup == 'y':
        destroy_result = client.destroy(force=True)
        
        if destroy_result.success:
            print(f"✅ {destroy_result.message}")
        else:
            print(f"❌ 清理失败: {destroy_result.error}")
    else:
        print("⏭️  跳过清理，Agent 继续运行")
        print("   可以使用以下命令手动清理:")
        print(f"   cd {init_result.project_path}")
        print("   agentkit destroy")
    
    print()
    print("=" * 70)
    print("✅ 工作流完成!")
    print("=" * 70)
    print()
    
    # ========== 总结 ==========
    print("📝 工作流总结:")
    print(f"   • 项目路径: {init_result.project_path}")
    print(f"   • 配置文件: {init_result.config_file}")
    print(f"   • 启动模式: {config.launch_type}")
    print(f"   • 镜像名称: {build_result.image_name if build_result.success else 'N/A'}")
    print(f"   • 服务端点: {deploy_result.endpoint_url if deploy_result.success else 'N/A'}")
    print()
    
    print("🎯 下一步操作:")
    print(f"   1. 查看项目文件: cd {init_result.project_path}")
    print(f"   2. 修改代码: vim {init_result.project_path}/{config.entry_point}")
    print(f"   3. 重新构建: cd {init_result.project_path} && agentkit build")
    print("   4. 查看状态: agentkit status")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
