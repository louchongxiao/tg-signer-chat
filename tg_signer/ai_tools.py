import base64
import json
import aiohttp
from typing import Optional

async def get_tongyi_client() -> Optional[aiohttp.ClientSession]:
    api_key = "sk-2be6a3c3a29148748a38afcba56ec3f6"
    if not api_key:
        return None
    return aiohttp.ClientSession(headers={"Authorization": f"Bearer {api_key}"})

async def choose_option_by_image(
    image: bytes,
    query: str,
    options: list[tuple[int, str]],
    client: aiohttp.ClientSession = None,
    model="qwen-vl-plus",
) -> int:
    client = client or await get_tongyi_client()
    if not client:
        return 0

    base64_image = base64.b64encode(image).decode("utf-8")
    messages = [
        {
            "role": "user",
            "content": [
                {"text": f"问题为：{query}, 选项为：{json.dumps(options)}。"},
                {"image": base64_image},
            ],
        }
    ]

    async with client.post(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        json={
            "model": model,
            "input": {"messages": messages},
            "parameters": {"result_format": "json"},
        },
    ) as response:
        result = await response.json()
        return int(result["output"]["choices"][0]["message"]["content"]["option"])

async def calculate_problem(
    query: str,
    client: aiohttp.ClientSession = None,
    model="qwen-plus",
) -> str:
    client = client or await get_tongyi_client()
    if not client:
        return ""

    messages = [
        {
            "role": "user",
            "content": f"问题是: {query}\n\n只需要给出答案，不要解释，不要输出任何其他内容。The answer is:",
        }
    ]

    async with client.post(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        json={
            "model": model,
            "input": {"messages": messages},
        },
    ) as response:
        result = await response.json()
        return result["output"]["choices"][0]["message"]["content"].strip()

async def get_reply(
    prompt: str,
    query: str,
    client: aiohttp.ClientSession = None,
    model="qwen-plus",
) -> str:
    client = client or await get_tongyi_client()
    if not client:
        return ""

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"{query}"},
    ]

    async with client.post(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        json={
            "model": model,
            "input": {"messages": messages},
        },
    )  as response:
        result = await response.json()
        # 添加响应结构校验
        if response.status != 200:
            raise ValueError(f"API请求失败: {result.get('message')}")
        try:
            return result["output"]["text"]
        except KeyError:
            print("DEBUG: 完整API响应 =>", result)  # 输出实际结构
            return "无法解析API响应"

