"""
Тесты для системы ИИ
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from ai_system import AISystem

class TestAISystem:
    """Тесты для AISystem"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.ai_system = AISystem()
    
    @pytest.mark.asyncio
    async def test_get_ai_response_greeting(self):
        """Тест ответа на приветствие"""
        response = await self.ai_system.get_ai_response("привет")
        
        assert response is not None
        assert len(response) > 0
        assert any(word in response.lower() for word in ['привет', 'hello', 'hi'])
    
    @pytest.mark.asyncio
    async def test_get_ai_response_question(self):
        """Тест ответа на вопрос"""
        response = await self.ai_system.get_ai_response("как дела?")
        
        assert response is not None
        assert len(response) > 0
        assert '?' in response or any(word in response.lower() for word in ['вопрос', 'думать'])
    
    @pytest.mark.asyncio
    async def test_get_ai_response_thanks(self):
        """Тест ответа на благодарность"""
        response = await self.ai_system.get_ai_response("спасибо")
        
        assert response is not None
        assert len(response) > 0
        assert any(word in response.lower() for word in ['пожалуйста', 'рад', 'помочь'])
    
    @pytest.mark.asyncio
    async def test_get_ai_response_default(self):
        """Тест ответа по умолчанию"""
        response = await self.ai_system.get_ai_response("случайное сообщение")
        
        assert response is not None
        assert len(response) > 0
        # Должен быть один из стандартных ответов
        default_responses = [
            "понимаю", "любопытно", "согласен", "наблюдение", 
            "круто", "идея", "стильно", "энергично"
        ]
        assert any(word in response.lower() for word in default_responses)
    
    @pytest.mark.asyncio
    async def test_generate_joke(self):
        """Тест генерации шутки"""
        joke = await self.ai_system.generate_joke()
        
        assert joke is not None
        assert len(joke) > 0
        assert "😂" in joke or "🤖" in joke or "😄" in joke
    
    @pytest.mark.asyncio
    async def test_generate_story(self):
        """Тест генерации истории"""
        story = await self.ai_system.generate_story()
        
        assert story is not None
        assert len(story) > 0
        assert "📚" in story or "🚀" in story or "🏰" in story
    
    @pytest.mark.asyncio
    async def test_generate_story_with_theme(self):
        """Тест генерации истории с темой"""
        theme = "космос"
        story = await self.ai_system.generate_story(theme)
        
        assert story is not None
        assert len(story) > 0
        assert theme.lower() in story.lower()
    
    @pytest.mark.asyncio
    async def test_get_ai_response_empty_string(self):
        """Тест ответа на пустую строку"""
        response = await self.ai_system.get_ai_response("")
        
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_get_ai_response_very_long_text(self):
        """Тест ответа на очень длинный текст"""
        long_text = "это очень длинное сообщение " * 100
        response = await self.ai_system.get_ai_response(long_text)
        
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_get_ai_response_special_characters(self):
        """Тест ответа на текст со специальными символами"""
        special_text = "Привет! Как дела? 😊 @username #hashtag"
        response = await self.ai_system.get_ai_response(special_text)
        
        assert response is not None
        assert len(response) > 0
    
    def test_system_prompt_contains_personality(self):
        """Проверяем, что системный промпт содержит личность"""
        prompt = self.ai_system._get_system_prompt("chat")
        assert "задорный" in prompt.lower()
    
    def test_clean_ai_response(self):
        """Проверяем очистку ответов от токенов"""
        text = self.ai_system._clean_ai_response("<s> [OUT] Привет! [/s]")
        assert "Привет" in text
    
    def test_generate_prompt_variants(self):
        assert "шутку" in self.ai_system._get_system_prompt("joke")
        assert "комплимент" in self.ai_system._get_system_prompt("compliment")
        assert "историю" in self.ai_system._get_system_prompt("story")
    
    def test_openrouter_models_iteration(self):
        """Проверяем, что метод вызывает OpenRouter и возвращает строку"""
        ai = AISystem()
        with patch.object(ai, '_call_openrouter', new_callable=AsyncMock) as mock_or:
            mock_or.return_value = "ok"
            import asyncio
            res = asyncio.get_event_loop().run_until_complete(ai.get_ai_response("hi"))
            assert res == "ok"
    
    def test_helpers_exist(self):
        assert callable(self.ai_system._clean_ai_response)
    
    def test_returns_string(self):
        import asyncio
        res = asyncio.get_event_loop().run_until_complete(self.ai_system.get_ai_response("привет"))
        assert isinstance(res, str)
    
    def test_prompt_contains_time_rules(self):
        prompt = self.ai_system._get_system_prompt("chat")
        assert "время" in prompt.lower()

class TestAISystemIntegration:
    """Интеграционные тесты для AISystem"""
    
    @pytest.mark.asyncio
    async def test_ai_system_with_mock_openrouter(self):
        """Тест системы ИИ с моком OpenRouter API"""
        ai_system = AISystem()
        
        with patch.object(ai_system, '_call_openrouter', new_callable=AsyncMock) as mock_or:
            mock_or.return_value = "Mocked OR response"
            response = await ai_system.get_ai_response("test question")
            mock_or.assert_called_once_with("test question", "chat")
            assert response == "Mocked OR response"

    @pytest.mark.asyncio
    async def test_ai_system_openrouter_error(self):
        """Тест обработки ошибок OpenRouter API"""
        ai_system = AISystem()
        
        with patch.object(ai_system, '_call_openrouter', new_callable=AsyncMock) as mock_or:
            mock_or.side_effect = Exception("OR error")
            response = await ai_system.get_ai_response("привет")
            assert response is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

