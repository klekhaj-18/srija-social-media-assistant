import anthropic

from backend.ai.prompts import SYSTEM_PROMPT, build_prompt


class ClaudeClient:
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate(
        self,
        content_type: str,
        context: str,
        tone: str,
        additional_instructions: str = "",
        conversation_history: list[dict] | None = None,
    ) -> dict:
        if conversation_history:
            messages = [{"role": m["role"], "content": m["content"]} for m in conversation_history]
            messages.append({"role": "user", "content": additional_instructions})
        else:
            prompt = build_prompt(content_type, context, tone, additional_instructions)
            messages = [{"role": "user", "content": prompt}]

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        return {
            "text": response.content[0].text,
            "provider": "claude",
            "model": self.model,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
        }
