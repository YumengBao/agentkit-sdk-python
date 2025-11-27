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
Strategy 层 - 纯粹的编排逻辑

Strategy 层只负责编排 Builder 和 Runner 的调用顺序，不包含：
- 错误处理（由 Executor 处理）
- 进度报告（由 Executor 处理）
- 日志记录（由 Executor 处理）
- 结果转换（Builder/Runner 直接返回标准 Result）

Strategy 是纯函数式的编排，易于测试和理解。
"""

from .base import Strategy
from .local_strategy import LocalStrategy
from .cloud_strategy import CloudStrategy
from .hybrid_strategy import HybridStrategy

__all__ = ['Strategy', 'LocalStrategy', 'CloudStrategy', 'HybridStrategy']
