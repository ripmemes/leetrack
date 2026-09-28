from openai import OpenAI
from models import db
from services.conversation_service import ConversationService


class AiTutorService:
    """Manages AI tutor interactions, prompt construction, and response guardrails."""

    def __init__(
        self, client: OpenAI, conversation_service: ConversationService, model_name: str = "groq/compound-mini"
    ) -> None:
        """Initializes the AiTutorService.

        Args:
            client: OpenAI compatible API client.
            conversation_service: Service managing conversation data.
            model_name: Target LLM model name.
        """
        self.client = client
        self.conversation_service = conversation_service
        self.model_name = model_name

    def chat(
        self,
        user_id: int,
        message_text: str,
        problem_id: int | None = None,
        conversation_id: int | None = None,
    ) -> tuple[str, int]:
        """Coordinates conversation state, sends messages to AI, and returns the response.

        Args:
            user_id: ID of the interacting user.
            message_text: User's question or message.
            problem_id: Optional ID of the LeetCode problem.
            conversation_id: Existing conversation ID or None.

        Returns:
            A tuple of (ai_reply, conversation_id).
        """
        convo = self.conversation_service.get_or_create_conversation(
            user_id=user_id, problem_id=problem_id, conversation_id=conversation_id
        )

        # 1. Record user message
        self.conversation_service.add_message(
            conversation_id=convo.id, user_id=user_id, role="user", content=message_text
        )

        # 2. Build Prompt History
        msgs = self.conversation_service.get_conversation_messages(convo.id, user_id)
        prompt = [
            {"role": "system", "content": f"Conversation ID: {convo.id}"},
            {
                "role": "system",
                "content": (
                    "You are an algorithm tutor. Do not provide full code. "
                    "Only give explanations, hints, and pseudocode."
                ),
            },
        ]
        for m in msgs:
            prompt.append({"role": m["role"], "content": m["content"]})

        # 3. Call LLM
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=prompt,
        )
        reply = response.choices[0].message.content or ""

        # 4. Guardrail: prevent code leaks
        if "```" in reply:
            reply = "⚠️ Debug reply: Full code is not allowed"

        # 5. Record assistant response & commit
        self.conversation_service.add_message(
            conversation_id=convo.id, user_id=user_id, role="assistant", content=reply
        )
        db.session.commit()

        # 6. Invalidate caches
        self.conversation_service.invalidate_cache(user_id, convo.id)

        return reply, convo.id
