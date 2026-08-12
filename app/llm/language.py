"""Shared language rules for LLM-facing product text."""

USER_FACING_ZH_RULE = (
    "语言要求：impact、hypothesis、reasoning_chain、steps[].action、comms_draft、thought "
    "等所有面向值班人的叙述必须使用简体中文。"
    "技术标识符（模型名、metric key、版本号、API/工具名、命令）可保留英文原文。"
)


def with_json_schema_instruction(schema_hint: str) -> str:
    return (
        f"只输出符合以下 schema 的合法 JSON，不要 markdown。{USER_FACING_ZH_RULE} "
        f"Schema: {schema_hint}"
    )
