import json
import httpx
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger
from app.models.question import QuestionModel
from app.schemas.ai import AITutorMessage

class LLMService:
    GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    @classmethod
    def _google_key(cls) -> Optional[str]:
        configured_key = settings.GOOGLE_API_KEY.strip()
        return configured_key or None

    @classmethod
    async def _call_google(cls, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 1000) -> Optional[str]:
        api_key = cls._google_key()
        if not api_key:
            return None

        system_instruction = next((message["content"] for message in messages if message["role"] == "system"), None)
        contents = [
            {
                "role": "model" if message["role"] == "assistant" else "user",
                "parts": [{"text": message["content"]}],
            }
            for message in messages
            if message["role"] != "system"
        ]
        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    cls.GOOGLE_API_URL.format(model=settings.GOOGLE_MODEL),
                    headers={"x-goog-api-key": api_key},
                    json=body,
                )
                if response.status_code == 200:
                    candidates = response.json().get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        return "".join(part.get("text", "") for part in parts).strip() or None
                else:
                    logger.warning(f"Google Gemini API returned status {response.status_code}: {response.text[:500]}")
        except Exception as error:
            logger.error(f"Error connecting to Google Gemini API: {error}")
        return None

    @classmethod
    async def generate_explanation(cls, question: QuestionModel, user_answer: str) -> Dict[str, str]:
        """
        Explains why user's answer is right or wrong, authoritatively grounded in PostgreSQL.
        """
        is_match = user_answer.strip().lower() == (question.correct_answer or "").strip().lower()
        
        system_prompt = (
            "You are a master academic teacher and tutor. "
            "A student just answered a question. Analyze their answer. "
            "CRITICAL: The database correct answer is authoritative and MUST NOT be contradicted. "
            "Return a clean JSON object with the following exact keys:\n"
            "{\n"
            '  "why_wrong": "Explanation of why the selected option is incorrect (or say \'Great job! You picked the correct answer.\' if correct)",\n'
            '  "why_correct": "Detailed explanation of why the correct answer is true and accurate",\n'
            '  "key_takeaway": "A concise, memorable summary or mnemonic to remember this concept",\n'
            '  "full_explanation": "A complete, educational breakdown that helps the student master this topic"\n'
            "}\n"
            "Return ONLY the JSON string."
        )

        user_prompt = (
            f"Question: {question.question_text}\n"
            f"Options: {question.options}\n"
            f"Authoritative Correct Answer: {question.correct_answer}\n"
            f"Authoritative Base Explanation: {question.explanation or 'None provided.'}\n"
            f"Subject: {question.subject} | Topic: {question.topic}\n"
            f"Student Selected Answer: {user_answer}\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        llm_reply = await cls._call_google(messages, temperature=0.1)

        if llm_reply:
            try:
                # Clean possible markdown block
                cleaned = llm_reply.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                parsed = json.loads(cleaned.strip())
                if all(k in parsed for k in ("why_wrong", "why_correct", "key_takeaway", "full_explanation")):
                    return parsed
            except Exception as parse_err:
                logger.warning(f"Could not parse Gemini JSON reply: {parse_err}. Content: {llm_reply}")

        # Fallback educational explanation
        if is_match:
            why_wrong = "Spot on! You selected the right answer."
            why_correct = question.explanation or f"'{question.correct_answer}' is the verified and correct answer for this topic."
            key_takeaway = f"Remember this key fact for {question.subject} ({question.topic})."
            full = f"Excellent! {question.explanation or 'Your answer aligns perfectly with the exam syllabus.'}"
        else:
            why_wrong = f"You selected '{user_answer}', which is incorrect based on official exam standards for {question.subject}."
            why_correct = question.explanation or f"'{question.correct_answer}' is the verified correct answer."
            key_takeaway = f"Core concept: In {question.topic}, the correct response is '{question.correct_answer}'."
            full = f"Explanation: {why_correct} Be careful not to confuse this with {user_answer}."

        return {
            "why_wrong": why_wrong,
            "why_correct": why_correct,
            "key_takeaway": key_takeaway,
            "full_explanation": full
        }

    @classmethod
    async def tutor_chat(
        cls,
        question: Optional[QuestionModel],
        user_message: str,
        chat_history: Optional[List[AITutorMessage]] = None
    ) -> str:
        """
        AI Tutor chatbot assisting students in resolving any doubts about questions or topics.
        """
        system_prompt = (
            "You are an encouraging, expert AI Educational Tutor helping a student. "
            "Be conversational, clear, and pedagodical. "
            "Use bullet points or concise paragraphs where helpful. "
            "Never contradict the authoritative database correct answer. "
            "If the student asks for mnemonics, simplified explanations, or examples, provide clear, intuitive ones."
        )

        context_lines = []
        if question:
            context_lines.append(f"Current Question: {question.question_text}")
            if question.options:
                context_lines.append(f"Options: {question.options}")
            if question.correct_answer:
                context_lines.append(f"Authoritative Correct Answer: {question.correct_answer}")
            if question.explanation:
                context_lines.append(f"Official Explanation: {question.explanation}")
            context_lines.append(f"Subject: {question.subject} | Topic: {question.topic}")
        
        context_str = "\n".join(context_lines)
        if context_str:
            system_prompt += f"\n\nAuthoritative Question Context:\n{context_str}"

        messages = [{"role": "system", "content": system_prompt}]

        if chat_history:
            for msg in chat_history[-6:]:  # Keep recent context
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_message})

        llm_reply = await cls._call_google(messages, temperature=0.3, max_tokens=800)
        if llm_reply:
            return llm_reply

        # Fallback tutor reply if offline / no key
        if question:
            return (
                f"Hello! Regarding **'{question.question_text}'**:\n\n"
                f"• The correct answer is **{question.correct_answer}**.\n"
                f"• Key Reason: {question.explanation or 'This is verified in the syllabus.'}\n"
                f"• Subject / Topic: **{question.subject}** → **{question.topic}**.\n\n"
                f"💡 *Tip:* To remember this easily, link **{question.topic}** directly with **{question.correct_answer}**. "
                f"Feel free to ask another doubt or ask for a real-world example!"
            )
        else:
            return (
                f"I'm your AI Quiz Tutor! I am here to help you understand questions, solve doubts, and prepare for exams. "
                f"Select a question from your quiz or ask me any concept you would like simplified!"
            )
