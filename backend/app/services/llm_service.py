import json
import httpx
from typing import List, Optional, Dict, Any, AsyncGenerator
from app.core.config import settings
from app.core.logging import logger
from app.models.question import QuestionModel
from app.schemas.ai import AITutorMessage

class LLMService:
    @classmethod
    def _nvidia_key(cls) -> Optional[str]:
        configured_key = settings.NVIDIA_API_KEY.strip()
        return configured_key or None

    @classmethod
    async def _call_nvidia(
        cls,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2000,
        model_override: Optional[str] = None
    ) -> Optional[str]:
        api_key = cls._nvidia_key()
        if not api_key:
            logger.warning("No NVIDIA_API_KEY available.")
            return None

        candidate_models = [model_override] if model_override else [settings.NVIDIA_MODEL]
        for fallback_m in settings.NVIDIA_FALLBACK_MODELS:
            if fallback_m not in candidate_models:
                candidate_models.append(fallback_m)

        url = f"{settings.NVIDIA_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        for model_name in candidate_models:
            body = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=15.0)) as client:
                    response = await client.post(url, headers=headers, json=body)
                    if response.status_code == 200:
                        data = response.json()
                        choices = data.get("choices", [])
                        if choices:
                            content = choices[0].get("message", {}).get("content", "")
                            if content and content.strip():
                                return content.strip()
                    else:
                        logger.warning(f"NVIDIA API with model {model_name} returned status {response.status_code}: {response.text[:300]}")
                        if response.status_code in (404, 410, 429, 503):
                            continue
            except Exception as error:
                logger.error(f"Error connecting to NVIDIA API with {model_name}: {error}")
                continue

        return None

    # Backward compatibility alias
    _call_google = _call_nvidia

    @classmethod
    async def stream_nvidia_content(
        cls,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        max_tokens: int = 4000
    ) -> AsyncGenerator[str, None]:
        """
        Streams response tokens in real-time from NVIDIA NIM using SSE streaming endpoint.
        """
        api_key = cls._nvidia_key()
        if not api_key:
            logger.warning("No NVIDIA_API_KEY available for streaming.")
            return

        candidate_models = [settings.NVIDIA_MODEL]
        for fallback_m in settings.NVIDIA_FALLBACK_MODELS:
            if fallback_m not in candidate_models:
                candidate_models.append(fallback_m)

        url = f"{settings.NVIDIA_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        for model_name in candidate_models:
            body = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            token_yielded = False

            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=15.0)) as client:
                    async with client.stream("POST", url, headers=headers, json=body) as response:
                        if response.status_code != 200:
                            error_body = await response.aread()
                            logger.warning(f"NVIDIA streaming with model {model_name} returned status {response.status_code}: {error_body.decode('utf-8', errors='ignore')[:300]}")
                            if response.status_code in (404, 410, 429, 503):
                                continue
                            return

                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            line_str = line.strip()
                            if line_str.startswith("data: "):
                                data_json = line_str[6:].strip()
                                if data_json == "[DONE]":
                                    break
                                try:
                                    payload = json.loads(data_json)
                                    choices = payload.get("choices", [])
                                    if choices:
                                        delta = choices[0].get("delta", {})
                                        chunk_text = delta.get("content", "")
                                        if chunk_text:
                                            token_yielded = True
                                            yield chunk_text
                                except json.JSONDecodeError:
                                    continue
                if token_yielded:
                    return
            except Exception as stream_err:
                logger.warning(f"Exception during NVIDIA streaming with {model_name}: {stream_err}")
                continue

    # Backward compatibility alias
    stream_gemini_content = stream_nvidia_content

    @classmethod
    async def generate_topic_quiz_questions(
        cls,
        topic: str,
        subject: Optional[str] = None,
        count: int = 5,
        difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Generates high quality MCQ questions for a specific topic using NVIDIA NIM when database does not have enough existing questions.
        """
        system_prompt = (
            "You are a master academic assessment designer. Create high-quality, conceptual, and pedagogical Multiple Choice Questions (MCQs). "
            "Output ONLY a valid JSON array of objects. Do not include markdown formatting or extra text outside the JSON array.\n"
            "Each object MUST have the following keys:\n"
            "[\n"
            "  {\n"
            '    "question_text": "Clear, concise question statement",\n'
            '    "options": ["A. First option", "B. Second option", "C. Third option", "D. Fourth option"],\n'
            '    "correct_answer": "A",\n'
            '    "explanation": "Detailed explanation of why this answer is correct",\n'
            '    "subject": "Subject name",\n'
            '    "chapter": "Chapter name",\n'
            '    "topic": "Topic name",\n'
            f'    "difficulty": "{difficulty.upper() if difficulty.upper() in ["EASY", "MEDIUM", "HARD"] else "MEDIUM"}"\n'
            "  }\n"
            "]"
        )
        user_prompt = (
            f"Generate exactly {count} distinct multiple-choice questions for the topic: '{topic}'"
            + (f" in the subject '{subject}'" if subject else "")
            + f" with difficulty level '{difficulty}'. "
            "Ensure options are labeled 'A. ...', 'B. ...', 'C. ...', 'D. ...' and correct_answer is just the single letter ('A', 'B', 'C', or 'D')."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        llm_reply = await cls._call_nvidia(messages, temperature=0.3, max_tokens=2500)
        if llm_reply:
            try:
                cleaned = llm_reply.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                parsed = json.loads(cleaned.strip())
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
            except Exception as parse_err:
                logger.warning(f"Could not parse NVIDIA generated quiz JSON: {parse_err}. Content: {llm_reply}")

        return []

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
        llm_reply = await cls._call_nvidia(messages, temperature=0.1)

        if llm_reply:
            try:
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
                logger.warning(f"Could not parse NVIDIA JSON reply: {parse_err}. Content: {llm_reply}")

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
            "Be conversational, clear, and pedagogical. "
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
            for msg in chat_history[-6:]:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_message})

        llm_reply = await cls._call_nvidia(messages, temperature=0.3, max_tokens=800)
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
