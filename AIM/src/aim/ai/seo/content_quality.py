"""
Content Quality Analyzer

N-E-E-A-T-T scoring based on Google quality guidelines.
"""

import re
from typing import List, Optional
from datetime import datetime, timedelta
from textblob import TextBlob

from ..llm.client import LLMClient
from ..llm.schemas import LLMRequest
from .schemas import ContentQualityScore


class ContentQualityAnalyzer:
    """
    Analyzes content quality using N-E-E-A-T-T framework.
    
    N-E-E-A-T-T:
    - Newsworthiness: Timeliness, relevance
    - Expertise: Author credentials, citations
    - Experience: First-hand knowledge, case studies
    - Authoritativeness: Domain authority, backlinks
    - Trustworthiness: HTTPS, privacy policy, contact info
    - Transparency: Clear authorship, disclosure
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize analyzer.
        
        Args:
            llm_client: LLM client for AI-powered analysis
        """
        self.llm_client = llm_client
    
    async def analyze(
        self,
        content: str,
        url: str,
        metadata: Optional[dict] = None,
    ) -> ContentQualityScore:
        """
        Analyze content quality.
        
        Args:
            content: Page content (HTML or plain text)
            url: Page URL
            metadata: Optional metadata (author, date, etc.)
        
        Returns:
            ContentQualityScore with N-E-E-A-T-T scores
        """
        # Extract text from HTML if needed
        text = self._extract_text(content)
        
        # Calculate individual scores
        newsworthiness = self._score_newsworthiness(text, metadata)
        expertise = self._score_expertise(text, metadata)
        experience = self._score_experience(text)
        authoritativeness = self._score_authoritativeness(url, metadata)
        trustworthiness = self._score_trustworthiness(url, content)
        transparency = self._score_transparency(content, metadata)
        readability = self._score_readability(text)
        
        # Calculate overall score (weighted average)
        overall = (
            newsworthiness * 0.15 +
            expertise * 0.20 +
            experience * 0.15 +
            authoritativeness * 0.15 +
            trustworthiness * 0.15 +
            transparency * 0.10 +
            readability * 0.10
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            text, url, metadata,
            newsworthiness, expertise, experience,
            authoritativeness, trustworthiness, transparency, readability
        )
        
        return ContentQualityScore(
            overall=round(overall, 1),
            newsworthiness=round(newsworthiness, 1),
            expertise=round(expertise, 1),
            experience=round(experience, 1),
            authoritativeness=round(authoritativeness, 1),
            trustworthiness=round(trustworthiness, 1),
            transparency=round(transparency, 1),
            readability=round(readability, 1),
            recommendations=recommendations,
        )
    
    def _extract_text(self, content: str) -> str:
        """Extract plain text from HTML."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', content)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _score_newsworthiness(self, text: str, metadata: Optional[dict]) -> float:
        """Score content timeliness and relevance."""
        score = 50.0  # Base score
        
        # Check publication date
        if metadata and 'date' in metadata:
            try:
                pub_date = datetime.fromisoformat(metadata['date'])
                days_old = (datetime.now() - pub_date).days
                
                if days_old < 30:
                    score += 30.0  # Very fresh
                elif days_old < 90:
                    score += 20.0  # Recent
                elif days_old < 365:
                    score += 10.0  # This year
                else:
                    score -= 10.0  # Old content
            except:
                pass
        
        # Check for date mentions in text
        date_patterns = [
            r'\d{4}',  # Year
            r'(январ|феврал|март|апрел|ма[йя]|июн|июл|август|сентябр|октябр|ноябр|декабр)',  # Russian months
            r'(сегодня|вчера|недавно|недели назад|месяц назад)',  # Relative dates
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 5.0
                break
        
        return min(score, 100.0)
    
    def _score_expertise(self, text: str, metadata: Optional[dict]) -> float:
        """Score author credentials and citations."""
        score = 30.0  # Base score
        
        # Check for author credentials
        if metadata and 'author' in metadata:
            score += 20.0
            
            # Check for credentials in author bio
            credentials = ['врач', 'доктор', 'профессор', 'кандидат', 'phd', 'md']
            author_text = metadata.get('author', '').lower()
            if any(cred in author_text for cred in credentials):
                score += 20.0
        
        # Check for citations
        citation_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\(\d{4}\)',  # (2024)
            r'источник:',
            r'исследование',
            r'по данным',
        ]
        
        citation_count = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in citation_patterns)
        score += min(citation_count * 5, 30.0)
        
        return min(score, 100.0)
    
    def _score_experience(self, text: str) -> float:
        """Score first-hand knowledge and case studies."""
        score = 40.0  # Base score
        
        # Check for first-person language
        first_person = ['я ', 'мы ', 'наш', 'мой', 'наши']
        if any(word in text.lower() for word in first_person):
            score += 15.0
        
        # Check for case studies
        case_study_keywords = [
            'пациент', 'клиент', 'случай', 'пример',
            'результат', 'до и после', 'отзыв'
        ]
        case_study_count = sum(text.lower().count(keyword) for keyword in case_study_keywords)
        score += min(case_study_count * 3, 30.0)
        
        # Check for specific details (numbers, dates, names)
        if re.search(r'\d+%', text):  # Percentages
            score += 5.0
        if re.search(r'\d+\s*(год|лет|месяц)', text):  # Time periods
            score += 5.0
        
        return min(score, 100.0)
    
    def _score_authoritativeness(self, url: str, metadata: Optional[dict]) -> float:
        """Score domain authority."""
        score = 50.0  # Base score
        
        # Check domain age (if available in metadata)
        if metadata and 'domain_age_years' in metadata:
            age = metadata['domain_age_years']
            if age > 5:
                score += 20.0
            elif age > 2:
                score += 10.0
        
        # Check for .ru or .рф domain (Russian market)
        if url.endswith('.ru') or url.endswith('.рф'):
            score += 10.0
        
        # Check for HTTPS
        if url.startswith('https://'):
            score += 10.0
        
        # Check for backlinks (if available in metadata)
        if metadata and 'backlinks' in metadata:
            backlinks = metadata['backlinks']
            if backlinks > 1000:
                score += 10.0
            elif backlinks > 100:
                score += 5.0
        
        return min(score, 100.0)
    
    def _score_trustworthiness(self, url: str, content: str) -> float:
        """Score security and privacy indicators."""
        score = 40.0  # Base score
        
        # Check HTTPS
        if url.startswith('https://'):
            score += 20.0
        
        # Check for privacy policy
        if 'политика конфиденциальности' in content.lower() or 'privacy policy' in content.lower():
            score += 15.0
        
        # Check for contact information
        contact_indicators = ['телефон', 'email', 'адрес', 'контакты']
        if any(indicator in content.lower() for indicator in contact_indicators):
            score += 15.0
        
        # Check for legal compliance (ФЗ-152 for Russia)
        if 'фз-152' in content.lower() or 'персональных данных' in content.lower():
            score += 10.0
        
        return min(score, 100.0)
    
    def _score_transparency(self, content: str, metadata: Optional[dict]) -> float:
        """Score authorship clarity and disclosure."""
        score = 50.0  # Base score
        
        # Check for author name
        if metadata and 'author' in metadata:
            score += 25.0
        
        # Check for author bio
        if 'об авторе' in content.lower() or 'автор:' in content.lower():
            score += 15.0
        
        # Check for disclosure/disclaimer
        disclosure_keywords = ['раскрытие', 'отказ от ответственности', 'disclaimer']
        if any(keyword in content.lower() for keyword in disclosure_keywords):
            score += 10.0
        
        return min(score, 100.0)
    
    def _score_readability(self, text: str) -> float:
        """Score text readability using Flesch-Kincaid."""
        try:
            blob = TextBlob(text)
            
            # Calculate average sentence length
            sentences = blob.sentences
            if not sentences:
                return 50.0
            
            words = blob.words
            avg_sentence_length = len(words) / len(sentences)
            
            # Calculate average syllables per word (approximation for Russian)
            avg_syllables = sum(self._count_syllables(str(word)) for word in words) / len(words)
            
            # Flesch Reading Ease (adapted for Russian)
            # Higher score = easier to read
            flesch_score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables
            
            # Normalize to 0-100 scale
            normalized = max(0, min(100, flesch_score))
            
            return normalized
        except:
            return 50.0  # Default if calculation fails
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)."""
        # Russian vowels
        vowels = 'аеёиоуыэюя'
        word = word.lower()
        count = sum(1 for char in word if char in vowels)
        return max(1, count)  # At least 1 syllable
    
    async def _generate_recommendations(
        self,
        text: str,
        url: str,
        metadata: Optional[dict],
        newsworthiness: float,
        expertise: float,
        experience: float,
        authoritativeness: float,
        trustworthiness: float,
        transparency: float,
        readability: float,
    ) -> List[str]:
        """Generate improvement recommendations using LLM."""
        # Build prompt with scores
        prompt = f"""Analyze this content quality assessment and provide 3-5 specific, actionable recommendations for improvement.

URL: {url}

Scores (0-100):
- Newsworthiness: {newsworthiness:.1f}
- Expertise: {expertise:.1f}
- Experience: {experience:.1f}
- Authoritativeness: {authoritativeness:.1f}
- Trustworthiness: {trustworthiness:.1f}
- Transparency: {transparency:.1f}
- Readability: {readability:.1f}

Content preview: {text[:500]}...

Provide recommendations in Russian, one per line, starting with a dash (-)."""
        
        try:
            request = LLMRequest(
                prompt=prompt,
                model="claude-sonnet-4",
                max_tokens=500,
                temperature=0.7,
            )
            
            response = await self.llm_client.generate(request)
            
            # Parse recommendations
            recommendations = []
            for line in response.content.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    recommendations.append(line[1:].strip())
            
            return recommendations[:5]  # Max 5 recommendations
        except:
            # Fallback recommendations based on lowest scores
            recommendations = []
            
            if newsworthiness < 60:
                recommendations.append("Добавьте дату публикации и регулярно обновляйте контент")
            if expertise < 60:
                recommendations.append("Укажите автора с его квалификацией и добавьте ссылки на источники")
            if experience < 60:
                recommendations.append("Добавьте кейсы и примеры из практики")
            if authoritativeness < 60:
                recommendations.append("Получите больше обратных ссылок от авторитетных сайтов")
            if trustworthiness < 60:
                recommendations.append("Добавьте политику конфиденциальности и контактную информацию")
            if transparency < 60:
                recommendations.append("Укажите информацию об авторе и раскройте возможные конфликты интересов")
            if readability < 60:
                recommendations.append("Упростите текст: используйте короткие предложения и простые слова")
            
            return recommendations[:5]
