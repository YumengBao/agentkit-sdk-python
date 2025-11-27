#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
从API JSON定义自动生成Pydantic结构体的工具

使用方法:
    python generate_types_from_api_json.py <json_file_path> [--output <output_file>]
    
示例:
    python generate_types_from_api_json.py ../agentkit/runtime/runtime_api.json --output generated_types.py \
        --base-class-name AgentKitBaseModel
"""

import json
import argparse
import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict


def sanitize_docstring(text: str) -> str:
    """清理docstring内容，避免三引号导致语法错误"""
    if not text:
        return ""
    sanitized = text.replace('"""', '\\"\\"\\"')
    sanitized = sanitized.replace('\r', ' ').replace('\n', ' ')
    sanitized = ' '.join(sanitized.split())
    return sanitized


class TypeMapper:
    """类型映射器：将JSON中的Type字段映射为Python类型"""
    
    TYPE_MAPPING = {
        1: "str",      # String
        2: "int",      # Integer
        3: "float",    # Float/Double
        4: "int",      # Long
        5: "float",    # Double
        6: "bool",     # Boolean
        7: "dict",     # Object/Map
        8: "list",     # Array (general)
    }
    
    @staticmethod
    def get_python_type(type_id: int) -> str:
        """获取Python类型字符串"""
        return TypeMapper.TYPE_MAPPING.get(type_id, "str")


class FieldInfo:
    """字段信息"""
    def __init__(self, name: str, python_name: str, type_str: str, 
                 is_required: bool, is_array: bool, description: str = ""):
        self.name = name  # 原始名称（用作alias）
        self.python_name = python_name  # Python字段名（小写+下划线）
        self.type_str = type_str  # Python类型字符串
        self.is_required = is_required
        self.is_array = is_array
        self.description = description
        
    def to_field_definition(self) -> str:
        """生成字段定义代码"""
        # 确定类型
        if self.is_array:
            final_type = f"list[{self.type_str}]"
        else:
            final_type = self.type_str
            
        # 处理可选字段
        if not self.is_required:
            final_type = f"Optional[{final_type}]"
            default_value = "default=None"
        else:
            default_value = "..."
            
        # 生成Field定义
        field_def = f'Field({default_value}, alias="{self.name}")'

        return f'    {self.python_name}: {final_type} = {field_def}'


class NestedModel:
    """嵌套模型"""
    def __init__(self, name: str):
        self.name = name
        self.fields: List[FieldInfo] = []
        self.children: Dict[str, 'NestedModel'] = {}
        
    def add_field(self, field: FieldInfo):
        """添加字段"""
        self.fields.append(field)
        
    def add_child(self, name: str) -> 'NestedModel':
        """添加子模型"""
        if name not in self.children:
            self.children[name] = NestedModel(name)
        return self.children[name]
        
    def to_class_definition(self, indent: int = 0, base_class_name: str = "BaseModel") -> str:
        """生成类定义"""
        indent_str = "    " * indent
        lines = []
        
        # 类定义
        lines.append(f"{indent_str}class {self.name}({base_class_name}):")
        
        # 字段定义
        if self.fields:
            for field in self.fields:
                lines.append(f"{indent_str}{field.to_field_definition()}")
        else:
            lines.append(f"{indent_str}    pass")
        
        return "\n".join(lines)


class APIStructGenerator:
    """API结构生成器"""
    
    def __init__(self, base_model_name: str = "AgentKitBaseModel", base_model_doc: str | None = None):
        self.nested_models: Dict[str, NestedModel] = {}
        self.used_types: Set[str] = {"BaseModel", "Field", "Optional"}
        self.generated_class_names: Set[str] = set()
        self.base_model_name = base_model_name
        self.base_model_doc = base_model_doc or "AgentKit auto-generated base model"
        # 确保基础类名不会与生成的结构体冲突
        self.generated_class_names.add(self.base_model_name)
        self.file_header_cache: List[str] | None = None

    def generate_client_module(
        self,
        data: dict,
        *,
        client_class_name: str,
        client_description: str,
        service_name: str,
        types_module: str,
        base_class_import: str,
        base_class_name: str,
    ) -> str:
        """根据API定义生成客户端代码"""
        api_list = data.get("ApiList", [])
        if not api_list:
            return ""
        lines = self._generate_file_header()
        lines.append("from typing import Dict")
        lines.append(f"from {base_class_import} import {base_class_name}")
        lines.append(f"from {types_module} import (")
        type_names = []
        for api in api_list:
            action = api.get("Action")
            if not action:
                continue
            type_names.extend([f"{action}Request", f"{action}Response"])
        for name in sorted(set(type_names)):
            lines.append(f"    {name},")
        lines.append(")")
        lines.append("")
        lines.append("")
        doc = sanitize_docstring(client_description or f"AgentKit client for {service_name}")
        lines.append(f"class {client_class_name}({base_class_name}):")
        lines.append(f"    \"\"\"{doc}\"\"\"")
        lines.append("    API_ACTIONS: Dict[str, str] = {")
        for api in api_list:
            action = api.get("Action")
            if not action:
                continue
            lines.append(f"        \"{action}\": \"{action}\",")
        lines.append("    }")
        lines.append("")
        lines.append("    def __init__(")
        lines.append("        self,")
        lines.append("        access_key: str = \"\",")
        lines.append("        secret_key: str = \"\",")
        lines.append("        region: str = \"\",")
        lines.append("        session_token: str = \"\",")
        lines.append("    ) -> None:")
        lines.append("        super().__init__(")
        lines.append("            access_key=access_key,")
        lines.append("            secret_key=secret_key,")
        lines.append("            region=region,")
        lines.append("            session_token=session_token,")
        lines.append(f"            service_name=\"{service_name}\",")
        lines.append("        )")
        lines.append("")
        for api in api_list:
            action = api.get("Action")
            if not action:
                continue
            method_name = self.to_snake_case(action)
            req_type = f"{action}Request"
            resp_type = f"{action}Response"
            lines.append("")
            lines.append(f"    def {method_name}(self, request: {req_type}) -> {resp_type}:")
            lines.append("        return self._invoke_api(")
            lines.append(f"            api_action=\"{action}\",")
            lines.append("            request=request,")
            lines.append(f"            response_type={resp_type},")
            lines.append("        )")
        lines.append("")
        return "\n".join(lines)

    def register_class_name(self, name: str):
        """记录已经生成的类名，避免重复"""
        self.generated_class_names.add(name)

    def qualify_model_name(self, base_name: str, action: str) -> str:
        """为嵌套模型生成带Action后缀的唯一类名"""
        candidate = f"{base_name}For{action}"
        index = 2
        while candidate in self.generated_class_names:
            candidate = f"{base_name}For{action}{index}"
            index += 1
        self.generated_class_names.add(candidate)
        return candidate

    def _strip_generic_suffix(self, name: str) -> str:
        """去掉一些通用后缀，使生成的类名更有语义，同时减少 *2 这类命名"""
        for suffix in ("Configuration", "Config", "Info", "List", "Item", "Items"):
            if name.endswith(suffix) and len(name) > len(suffix):
                return name[: -len(suffix)]
        return name

    def _build_nested_base_name(self, path: str, is_array_object: bool) -> str:
        """根据字段路径构造嵌套模型的基础类名，尽量避免使用 *2 这种后缀"""
        parts = [self._strip_generic_suffix(p) for p in path.split(".") if p]
        if not parts:
            core = "NestedModel"
        elif len(parts) == 1:
            core = parts[0]
        else:
            # 多级嵌套时，将各层名称拼接起来以区分不同路径
            core = "".join(parts)
        if is_array_object:
            core = f"{core}Item"
        return core

    def parse_field_path(self, field_name: str) -> Tuple[List[str], str, bool, bool]:
        """
        解析字段路径
        
        返回: (path_parts, field_name, is_array_item, is_simple_array)
        例如:
            "Name" -> ([], "Name", False, False)
            "AuthorizerConfiguration.KeyAuth.ApiKey" -> (["AuthorizerConfiguration", "KeyAuth"], "ApiKey", False, False)
            "Envs.N.Key" -> (["Envs"], "Key", True, False) - 对象数组的字段
            "AllowedClients.N" -> (["AuthorizerConfiguration", "CustomJwtAuthorizer"], "AllowedClients", False, True) - 简单数组字段
        """
        parts = field_name.split(".")
        
        # 检查是否以.N结尾（简单数组）
        is_simple_array = len(parts) >= 2 and parts[-1] == "N"
        
        # 检查是否包含.N.（对象数组）
        is_array_item = "N" in parts[:-1] if len(parts) > 1 else False
        
        # 清理N标记
        clean_parts = []
        for part in parts:
            if part != "N":
                clean_parts.append(part)
        
        if len(clean_parts) == 1:
            return [], clean_parts[0], False, False
        else:
            return clean_parts[:-1], clean_parts[-1], is_array_item, is_simple_array
    
    def to_snake_case(self, name: str) -> str:
        """将驼峰命名转换为蛇形命名"""
        if not name:
            return name
        # 先在连续大写 + 小写的边界处插入下划线，例如 "MCPService" -> "MCP_Service"
        step_one = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        # 再在小写/数字后接大写的地方插入下划线，例如 "ServiceID" -> "Service_ID"
        step_two = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", step_one)
        # 统一转小写并去掉可能的重复下划线
        return re.sub(r"__+", "_", step_two).lower()
    
    def create_nested_structure(self, parameters: List[dict], action: str) -> NestedModel:
        """创建嵌套结构"""
        root = NestedModel("Root")
        path_models: Dict[str, NestedModel] = {}
        class_models: Dict[str, NestedModel] = {}
        path_class_names: Dict[str, str] = {}
        
        # 第一遍：收集所有嵌套路径和数组字段
        array_fields = defaultdict(set)  # 记录哪些路径有数组字段（.N.）
        normal_fields = defaultdict(set)  # 记录哪些路径有普通字段
        nested_object_paths = set()  # 记录所有嵌套对象路径
        
        for param in parameters:
            field_name = param["Name"]
            path_parts, final_name, is_array_item, is_simple_array = self.parse_field_path(field_name)
            
            if len(path_parts) > 0:
                path_str = ".".join(path_parts)
                
                if is_array_item:
                    # 记录这是一个对象数组的字段
                    array_fields[path_str].add(final_name)
                else:
                    # 记录这是一个普通字段
                    normal_fields[path_str].add(final_name)
                
                # 记录所有嵌套路径
                for i in range(1, len(path_parts) + 1):
                    nested_path = ".".join(path_parts[:i])
                    nested_object_paths.add(nested_path)
        
        # 判断哪些路径是真正的数组对象（只有数组字段，没有普通字段）
        array_objects = {}
        for path in array_fields:
            if path not in normal_fields:
                # 这个路径只有数组字段，是真正的数组对象
                array_objects[path] = array_fields[path]
        
        # 创建嵌套模型实例（先创建普通嵌套对象）
        for path in sorted(nested_object_paths):
            if path not in array_objects:  # 如果不是数组对象路径
                base_name = self._build_nested_base_name(path, is_array_object=False)
                model_name = self.qualify_model_name(base_name, action)
                model = NestedModel(model_name)
                path_models[path] = model
                path_class_names[path] = model_name
                class_models[model_name] = model
        
        # 为数组对象创建Item模型（只有在根级别或明确的数组对象才加Item后缀）
        for array_path in array_objects:
            parts = array_path.split(".")
            if len(parts) == 1 or array_path in nested_object_paths:
                base_name = self._build_nested_base_name(array_path, is_array_object=True)
            else:
                # 忽略那些仅作为中间路径、但本身不是嵌套对象的数组路径
                continue
            model_name = self.qualify_model_name(base_name, action)
            model = NestedModel(model_name)
            path_models[array_path] = model
            path_class_names[array_path] = model_name
            class_models[model_name] = model

        # 调试：打印 CreateMCPToolset 的嵌套路径信息
        if action == "CreateMCPToolset":
            print("[DEBUG] action=CreateMCPToolset nested_object_paths=", sorted(nested_object_paths))
            print("[DEBUG] action=CreateMCPToolset array_objects=", sorted(array_objects.keys()))

        # 建立父子关系字段（包含对象和对象数组）
        for full_path in sorted(nested_object_paths):
            parts = full_path.split(".")
            if len(parts) < 2:
                # 顶层对象由 root_refs 负责挂到根上
                continue
            parent_path = ".".join(parts[:-1])
            child_name = parts[-1]
            if parent_path not in path_models:
                continue
            parent_model = path_models[parent_path]
            child_python_name = self.to_snake_case(child_name)
            existing = [f for f in parent_model.fields if f.python_name == child_python_name]
            if existing:
                continue
            child_type = path_class_names.get(full_path, child_name)
            is_array_object = full_path in array_objects
            field = FieldInfo(
                name=child_name,
                python_name=child_python_name,
                type_str=child_type,
                is_required=False,
                is_array=is_array_object,
                description="",
            )
            parent_model.add_field(field)

        # 调试：打印 CreateMCPToolset 的父子关系字段
        if action == "CreateMCPToolset":
            for p, m in path_models.items():
                print(
                    "[DEBUG] path_model",
                    p,
                    "-> class",
                    m.name,
                    "fields=",
                    [f.python_name for f in m.fields],
                )

        # 第二遍：填充字段
        root_refs = {}  # 用于跟踪根级别的对象引用
        
        for param in parameters:
            field_name = param["Name"]
            path_parts, final_name, is_array_item, is_simple_array = self.parse_field_path(field_name)
            
            # 获取类型
            type_id = param.get("Type", 1)
            python_type = TypeMapper.get_python_type(type_id)
            
            # 是否必填
            is_required = param.get("IsRequired", 0) == 1
            
            # 描述
            description = param.get("Description", "")
            
            python_name = self.to_snake_case(final_name)
            
            # 处理不同情况
            if len(path_parts) == 0:
                # 根级别的简单字段（不是嵌套对象的入口）
                field = FieldInfo(
                    name=final_name,
                    python_name=python_name,
                    type_str=python_type,
                    is_required=is_required,
                    is_array=False,
                    description=description
                )
                root.add_field(field)
                
            elif is_simple_array:
                # 这是一个简单数组字段（如AuthorizerConfiguration.CustomJwtAuthorizer.AllowedClients.N）
                parent_path = ".".join(path_parts)
                if parent_path in path_models:
                    parent_model = path_models[parent_path]
                    existing = [f for f in parent_model.fields if f.python_name == python_name]
                    if not existing:
                        field = FieldInfo(
                            name=final_name,
                            python_name=python_name,
                            type_str=python_type,
                            is_required=is_required,
                            is_array=True,
                            description=description
                        )
                        parent_model.add_field(field)
                elif len(path_parts) == 0:
                    # 根级别的简单数组
                    field = FieldInfo(
                        name=final_name,
                        python_name=python_name,
                        type_str=python_type,
                        is_required=is_required,
                        is_array=True,
                        description=description
                    )
                    root.add_field(field)
                
            elif is_array_item:
                # 这是对象数组的字段（如Envs.N.Key）
                array_path = ".".join(path_parts)
                
                if array_path in path_models:
                    field = FieldInfo(
                        name=final_name,
                        python_name=python_name,
                        type_str=python_type,
                        is_required=is_required,
                        is_array=False,
                        description=description
                    )
                    path_models[array_path].add_field(field)
                    
                    # 确保根级别有对这个数组的引用
                    if len(path_parts) == 1:
                        array_name = path_parts[0]
                        if array_name not in root_refs:
                            ref_type = path_class_names.get(array_path, f"{array_name}Item")
                            root_refs[array_name] = {
                                'type': ref_type,
                                'is_array': True,
                                'is_required': False
                            }
            else:
                # 嵌套对象字段本身携带的简单属性（非子对象引用）
                full_path = ".".join(path_parts)

                if full_path in path_models:
                    field = FieldInfo(
                        name=final_name,
                        python_name=python_name,
                        type_str=python_type,
                        is_required=is_required,
                        is_array=False,
                        description=description,
                    )
                    path_models[full_path].add_field(field)

                # 确保根级别的第一层对象被引用
                root_level_name = path_parts[0]
                if root_level_name not in root_refs:
                    ref_type = path_class_names.get(root_level_name, root_level_name)
                    root_refs[root_level_name] = {
                        'type': ref_type,
                        'is_array': False,
                        'is_required': False,
                    }
        
        # 添加根级别的对象引用
        for ref_name, ref_info in root_refs.items():
            python_name = self.to_snake_case(ref_name)
            # 检查是否已存在
            existing = [f for f in root.fields if f.python_name == python_name]
            if not existing:
                ref_type = ref_info['type']
                field = FieldInfo(
                    name=ref_name,
                    python_name=python_name,
                    type_str=ref_type,
                    is_required=ref_info['is_required'],
                    is_array=ref_info['is_array'],
                    description=""
                )
                root.add_field(field)
        
        self.nested_models = class_models
        return root
    
    def generate_request_model(self, action: str, parameters: List[dict]) -> str:
        """生成请求模型"""
        class_name = f"{action}Request"
        self.register_class_name(class_name)
        root = self.create_nested_structure(parameters, action)
        root.name = class_name
        
        sections = []
        for model in self.nested_models.values():
            sections.append(model.to_class_definition(base_class_name=self.base_model_name))
        sections.append(root.to_class_definition(base_class_name=self.base_model_name))
        
        return "\n\n".join(sections)
    
    def generate_response_model(self, action: str, parameters: List[dict]) -> str:
        """生成响应模型"""
        class_name = f"{action}Response"
        if class_name in self.generated_class_names:
            # 如果已经存在同名响应，跳过生成以避免重复
            return ""
        self.register_class_name(class_name)
        
        lines = []
        lines.append(f"class {class_name}({self.base_model_name}):")
        
        # 处理响应字段
        has_fields = False
        for param in parameters:
            name = param.get("Name", "")
            type_id = param.get("Type", 1)
            is_array = param.get("IsArray", 0) == 1
            description = param.get("Description", "")
            param_type_ref = param.get("ParameterType", {}).get("$ref", "")
            
            python_name = self.to_snake_case(name)
            
            # 确定类型
            if param_type_ref:
                # 引用DataType中定义的类型
                python_type = param_type_ref
            else:
                python_type = TypeMapper.get_python_type(type_id)
            
            # 处理数组
            if is_array:
                python_type = f"list[{python_type}]"
            
            # 响应字段通常都是可选的
            python_type = f"Optional[{python_type}]"
            
            # 生成字段定义
            field_def = f'Field(default=None, alias="{name}")'

            lines.append(f'    {python_name}: {python_type} = {field_def}')
            has_fields = True
        
        if not has_fields:
            lines.append("    pass")
        
        return "\n".join(lines)
    
    def generate_datatype_models(self, data_types: List[dict]) -> List[str]:
        """从DataType节生成模型定义"""
        lines = []
        
        for i, dtype in enumerate(data_types):
            struct_name = dtype.get("StructName", "")
            elements = dtype.get("Element", [])
            
            if not struct_name or not elements:
                continue
            if struct_name in self.generated_class_names:
                continue
            self.register_class_name(struct_name)
            
            # 添加空行分隔不同的类（除了第一个）
            if i > 0:
                lines.append("")
                lines.append("")
            
            # 生成类定义
            lines.append(f"class {struct_name}({self.base_model_name}):")
            
            # 生成字段
            for element in elements:
                elem_name = element.get("ElementName", "")
                elem_type = element.get("ElementType", 1)
                is_required = element.get("IsRequired", 0) == 1
                is_array = element.get("IsArray", 0) == 1
                param_type_ref = element.get("ParameterType", {}).get("$ref", "")
                
                python_name = self.to_snake_case(elem_name)
                
                # 确定类型
                if param_type_ref:
                    # 引用其他类型
                    python_type = param_type_ref
                else:
                    python_type = TypeMapper.get_python_type(elem_type)
                
                # 处理数组
                if is_array:
                    python_type = f"list[{python_type}]"
                
                # 处理可选
                if not is_required:
                    python_type = f"Optional[{python_type}]"
                    default_value = "default=None"
                else:
                    default_value = "..."
                
                lines.append(f'    {python_name}: {python_type} = Field({default_value}, alias="{elem_name}")')
            
        
        return lines

    def _generate_file_header(self) -> List[str]:
        """生成通用文件头"""
        if self.file_header_cache is not None:
            return list(self.file_header_cache)
        lines = []
        lines.append("# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.")
        lines.append("#")
        lines.append("# Licensed under the Apache License, Version 2.0 (the \"License\");")
        lines.append("# you may not use this file except in compliance with the License.")
        lines.append("# You may obtain a copy of the License at")
        lines.append("#")
        lines.append("#     http://www.apache.org/licenses/LICENSE-2.0")
        lines.append("#")
        lines.append("# Unless required by applicable law or agreed to in writing, software")
        lines.append("# distributed under the License is distributed on an \"AS IS\" BASIS,")
        lines.append("# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.")
        lines.append("# See the License for the specific language governing permissions and")
        lines.append("# limitations under the License.")
        lines.append("")
        lines.append("# Auto-generated from API JSON definition")
        lines.append("# Do not edit manually")
        lines.append("")
        lines.append("from __future__ import annotations")
        lines.append("")
        self.file_header_cache = lines
        return list(lines)
    
    def generate_from_api_json(self, data: dict) -> str:
        """从API JSON数据生成所有模型"""
        lines = self._generate_file_header()
        lines.append("from typing import Optional")
        lines.append("from pydantic import BaseModel, Field")
        lines.append("")
        lines.append("\n".join([
            f"class {self.base_model_name}(BaseModel):",
            f"    \"\"\"{self.base_model_doc}\"\"\"",
            "    model_config = {",
            '        "populate_by_name": True,',
            '        "arbitrary_types_allowed": True',
            "    }",
        ]))
        lines.append("")
        lines.append("")
        # 首先生成DataType中定义的结构体
        data_types = data.get("DataType")
        if data_types:
            lines.append("# Data Types")
            datatype_lines = self.generate_datatype_models(data_types)
            lines.extend(datatype_lines)
            lines.append("")
            lines.append("")
        
        # 处理每个API
        api_list = data.get("ApiList", [])
        for api in api_list:
            action = api.get("Action", "")
            request_params = api.get("RequestParameters", [])
            response_params = api.get("ResponseParameters", [])
            
            # 生成请求模型
            if request_params:
                lines.append(f"# {action} - Request")
                lines.append(self.generate_request_model(action, request_params))
                lines.append("")
                lines.append("")
            
            # 生成响应模型
            if response_params:
                lines.append(f"# {action} - Response")
                lines.append(self.generate_response_model(action, response_params))
                lines.append("")
                lines.append("")
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="从API JSON定义生成Pydantic结构体"
    )
    parser.add_argument(
        "json_file",
        help="API JSON定义文件路径"
    )
    parser.add_argument(
        "--output", "-o",
        default="generated_types.py",
        help="类型定义输出文件 (默认: generated_types.py)"
    )
    parser.add_argument(
        "--client-output",
        help="可选：客户端代码输出文件路径"
    )
    parser.add_argument(
        "--client-class-name",
        help="可选：客户端类名，例如 AgentkitMCP"
    )
    parser.add_argument(
        "--client-description",
        help="可选：客户端类的docstring描述"
    )
    parser.add_argument(
        "--service-name",
        help="可选：服务名称，用于BaseAgentkitClient(service_name=...)"
    )
    parser.add_argument(
        "--types-module",
        help="可选：客户端引用的类型模块（例如 agentkit.mcp.mcp_all_types）"
    )
    parser.add_argument(
        "--base-class-import",
        default="agentkit.client",
        help="基础客户端类的导入路径 (默认: agentkit.client)"
    )
    parser.add_argument(
        "--base-client-class",
        default="BaseAgentkitClient",
        help="客户端基类名称 (默认: BaseAgentkitClient)"
    )
    parser.add_argument(
        "--base-class-name",
        default="AgentKitBaseModel",
        help="生成模型继承的基础类名称 (默认: AgentKitBaseModel)"
    )
    parser.add_argument(
        "--base-class-doc",
        default="AgentKit auto-generated base model",
        help="基础类的文档字符串 (默认: AgentKit auto-generated base model)"
    )
    
    args = parser.parse_args()
    
    # 生成代码
    with open(args.json_file, 'r', encoding='utf-8') as f:
        api_data = json.load(f)

    generator = APIStructGenerator(
        base_model_name=args.base_class_name,
        base_model_doc=args.base_class_doc,
    )
    generated_code = generator.generate_from_api_json(api_data)
    
    # 写入文件
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(generated_code)
    
    print(f"✓ 成功生成结构体定义: {args.output}")
    print(f"  - 从: {args.json_file}")
    print(f"  - 共生成 {len(generated_code.splitlines())} 行代码")

    if args.client_output:
        required_client_args = [
            args.client_class_name,
            args.service_name,
            args.types_module,
        ]
        if not all(required_client_args):
            missing = [
                name for name, value in [
                    ("--client-class-name", args.client_class_name),
                    ("--service-name", args.service_name),
                    ("--types-module", args.types_module),
                ] if not value
            ]
            missing_str = ", ".join(missing)
            raise ValueError(f"缺少生成客户端所需参数: {missing_str}")
        client_code = generator.generate_client_module(
            api_data,
            client_class_name=args.client_class_name,
            client_description=args.client_description or "",
            service_name=args.service_name,
            types_module=args.types_module,
            base_class_import=args.base_class_import,
            base_class_name=args.base_client_class,
        )
        with open(args.client_output, 'w', encoding='utf-8') as f:
            f.write(client_code)
        print(f"✓ 成功生成客户端: {args.client_output}")
        print(f"  - From: {args.json_file}")
        print(f"  - Lines: {len(client_code.splitlines())}")


if __name__ == "__main__":
    main()
