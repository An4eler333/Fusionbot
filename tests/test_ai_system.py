"""
Тесты для системы ИИ
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

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
    
    def test_local_response_greeting_variations(self):
        """Тест различных вариантов приветствий"""
        greetings = ["привет", "hello", "hi", "здравствуй", "Привет!", "HELLO"]
        
        for greeting in greetings:
            response = self.ai_system._get_local_response(greeting, "chat")
            assert response is not None
            assert len(response) > 0
            assert any(word in response.lower() for word in ['привет', 'hello', 'hi'])
    
    def test_local_response_question_variations(self):
        """Тест различных вариантов вопросов"""
        questions = ["что это?", "как дела?", "когда?", "где?", "почему?"]
        
        for question in questions:
            response = self.ai_system._get_local_response(question, "chat")
            assert response is not None
            assert len(response) > 0
            assert '?' in response or any(word in response.lower() for word in ['вопрос', 'думать'])
    
    def test_local_response_thanks_variations(self):
        """Тест различных вариантов благодарностей"""
        thanks = ["спасибо", "thanks", "thx", "благодарю", "Спасибо!"]
        
        for thank in thanks:
            response = self.ai_system._get_local_response(thank, "chat")
            assert response is not None
            assert len(response) > 0
            assert any(word in response.lower() for word in ['пожалуйста', 'рад', 'помочь'])
    
    def test_local_response_contexts(self):
        """Тест различных контекстов"""
        contexts = ["joke", "story", "compliment"]
        
        for context in contexts:
            response = self.ai_system._get_local_response("test", context)
            assert response is not None
            assert len(response) > 0
    
    def test_generate_local_joke_content(self):
        """Тест содержания локальных шуток"""
        joke = self.ai_system._generate_local_joke()
        
        assert joke is not None
        assert len(joke) > 0
        # Проверяем что это действительно шутка
        assert "😂" in joke or "🤖" in joke or "😄" in joke
        assert "\n" in joke  # Шутки обычно многострочные
    
    def test_generate_local_story_content(self):
        """Тест содержания локальных историй"""
        story = self.ai_system._generate_local_story()
        
        assert story is not None
        assert len(story) > 0
        # Проверяем что это действительно история
        assert "📚" in story or "🚀" in story or "🏰" in story
        assert len(story) > 50  # Истории должны быть достаточно длинными
    
    def test_generate_local_compliment_content(self):
        """Тест содержания локальных комплиментов"""
        compliment = self.ai_system._generate_local_compliment()
        
        assert compliment is not None
        assert len(compliment) > 0
        # Проверяем что это действительно комплимент
        assert any(word in compliment.lower() for word in ['звезда', 'юмор', 'энергия', 'драгоценный'])

class TestAISystemIntegration:
    """Интеграционные тесты для AISystem"""
    
    @pytest.mark.asyncio
    async def test_ai_system_with_mock_groq(self):
        """Тест системы ИИ с моком Groq API"""
        ai_system = AISystem()
        
        # Мокаем Groq API
        with patch.object(ai_system, '_call_groq', new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = "Mocked Groq response"
            
            response = await ai_system.get_ai_response("test question")
            
            # Проверяем что Groq был вызван
            mock_groq.assert_called_once_with("test question", "chat")
            assert response == "Mocked Groq response"
    
    @pytest.mark.asyncio
    async def test_ai_system_groq_fallback(self):
        """Тест fallback при недоступности Groq"""
        ai_system = AISystem()
        
        # Мокаем Groq API чтобы он возвращал None (недоступен)
        with patch.object(ai_system, '_call_groq', new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = None
            
            response = await ai_system.get_ai_response("привет")
            
            # Проверяем что использовался fallback
            mock_groq.assert_called_once()
            assert response is not None
            assert response != "Mocked Groq response"
            # Должен быть локальный ответ
            assert any(word in response.lower() for word in ['привет', 'hello', 'hi'])
    
    @pytest.mark.asyncio
    async def test_ai_system_groq_error_handling(self):
        """Тест обработки ошибок Groq API"""
        ai_system = AISystem()
        
        # Мокаем Groq API чтобы он выбрасывал исключение
        with patch.object(ai_system, '_call_groq', new_callable=AsyncMock) as mock_groq:
            mock_groq.side_effect = Exception("Groq API error")
            
            response = await ai_system.get_ai_response("test")
            
            # Проверяем что ошибка была обработана и использован fallback
            mock_groq.assert_called_once()
            assert response is not None
            # Должен быть локальный ответ
            assert len(response) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

