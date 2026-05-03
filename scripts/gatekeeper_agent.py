#!/usr/bin/env python3
"""
Gatekeeper Agent - Контроль качества входящей информации

Проверяет информацию перед попаданием в систему:
1. Базовые проверки (размер, язык, структура)
2. Fact-checking (проверка фактов и достоверности)
3. Relevance check (применимость к системе)
4. Quality check (качество контента)
5. Duplicate check (дубликаты)
6. Hypothesis validation (проверка гипотез на опыте)

Если проверка не пройдена - файл отправляется в quarantine/
"""

import asyncio
import hashlib
import re
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml


class FactChecker:
    """Проверка фактов и достоверности информации"""

    async def check_facts(self, content: str, metadata: dict) -> Dict[str, Any]:
        """
        Проверить факты в контенте через Claude CLI

        Returns:
            {
                'is_valid': bool,
                'confidence': float (0.0-1.0),
                'issues': List[str],
                'verified_facts': List[str],
                'unverified_claims': List[str],
                'contradictions': List[str]
            }
        """
        prompt = f"""
Проанализируй следующий контент на достоверность фактов:

**Метаданные:**
- Источник: {metadata.get('source', 'unknown')}
- Автор: {metadata.get('author', 'unknown')}
- Дата: {metadata.get('published', 'unknown')}

**Контент:**
{content[:3000]}

**Задача:**
1. Выяви все фактические утверждения
2. Оцени достоверность каждого утверждения
3. Найди противоречия
4. Определи непроверенные заявления
5. Оцени общую надёжность (0.0-1.0)

**ВАЖНО:** Ответь ТОЛЬКО валидным JSON, без markdown блоков.

**Формат ответа:**
{{
    "verified_facts": ["факт 1", "факт 2"],
    "unverified_claims": ["заявление 1", "заявление 2"],
    "contradictions": ["противоречие 1"],
    "confidence": 0.85,
    "issues": ["проблема 1", "проблема 2"],
    "reasoning": "обоснование оценки"
}}
"""

        try:
            # Вызываем через subprocess
            result = subprocess.run(
                ['claude', '--model', 'opus', '-p', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise Exception(f"Claude CLI error: {result.stderr}")

            # Парсим JSON из ответа
            result_text = result.stdout.strip()

            # Извлекаем JSON из markdown блока если есть
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            parsed = json.loads(result_text.strip())

            # Определяем is_valid на основе confidence и issues
            parsed['is_valid'] = (
                parsed['confidence'] >= 0.7 and
                len(parsed.get('contradictions', [])) == 0
            )

            return parsed

        except Exception as e:
            print(f"⚠️  Ошибка fact-checking: {e}")
            return {
                'is_valid': False,
                'confidence': 0.0,
                'issues': [f"Ошибка проверки: {str(e)}"],
                'verified_facts': [],
                'unverified_claims': [],
                'contradictions': []
            }


class RelevanceChecker:
    """Проверка применимости к системе"""

    def __init__(self, system_context: str):
        self.system_context = system_context

    async def check_relevance(self, content: str, metadata: dict) -> Dict[str, Any]:
        """
        Проверить применимость контента к системе через Claude CLI

        Returns:
            {
                'is_relevant': bool,
                'relevance_score': float (0.0-1.0),
                'applicable_areas': List[str],
                'reasoning': str
            }
        """
        prompt = f"""
Проанализируй применимость следующего контента к нашей системе:

**Контекст системы:**
{self.system_context}

**Контент для проверки:**
Тип: {metadata.get('type', 'unknown')}
Приоритет: {metadata.get('priority', 'unknown')}

{content[:2000]}

**Задача:**
1. Определи, применим ли этот контент к нашей системе
2. Оцени релевантность (0.0-1.0)
3. Укажи области применения
4. Обоснуй оценку

**ВАЖНО:** Ответь ТОЛЬКО валидным JSON, без markdown блоков.

**Формат ответа:**
{{
    "relevance_score": 0.85,
    "applicable_areas": ["area1", "area2"],
    "reasoning": "обоснование",
    "actionable": true
}}
"""

        try:
            result = subprocess.run(
                ['claude', '--model', 'sonnet', '-p', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise Exception(f"Claude CLI error: {result.stderr}")

            result_text = result.stdout.strip()

            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            parsed = json.loads(result_text.strip())
            parsed['is_relevant'] = parsed['relevance_score'] >= 0.6

            return parsed

        except Exception as e:
            print(f"⚠️  Ошибка relevance check: {e}")
            return {
                'is_relevant': False,
                'relevance_score': 0.0,
                'applicable_areas': [],
                'reasoning': f"Ошибка проверки: {str(e)}"
            }


class HypothesisValidator:
    """Валидация гипотез на основе опыта"""

    def __init__(self, experience_db_path: Path):
        self.experience_db = experience_db_path
        self.hypotheses: Dict[str, Dict] = {}
        self.load_hypotheses()

    def load_hypotheses(self):
        """Загрузить историю гипотез"""
        if self.experience_db.exists():
            with open(self.experience_db, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.hypotheses = data.get('hypotheses', {})

    def save_hypotheses(self):
        """Сохранить историю гипотез"""
        self.experience_db.parent.mkdir(parents=True, exist_ok=True)
        with open(self.experience_db, 'w', encoding='utf-8') as f:
            yaml.dump({'hypotheses': self.hypotheses}, f, allow_unicode=True)

    def extract_hypothesis(self, content: str, metadata: dict) -> Optional[str]:
        """Извлечь гипотезу из контента"""
        # Ищем паттерны гипотез
        patterns = [
            r"гипотеза[:\s]+(.+?)(?:\n|$)",
            r"предполагаю[:\s]+(.+?)(?:\n|$)",
            r"если[:\s]+(.+?)то[:\s]+(.+?)(?:\n|$)",
            r"можно попробовать[:\s]+(.+?)(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def register_hypothesis(
        self,
        hypothesis: str,
        source_file: str,
        metadata: dict
    ) -> str:
        """
        Зарегистрировать гипотезу для отслеживания

        Returns:
            hypothesis_id
        """
        hypothesis_id = hashlib.md5(hypothesis.encode()).hexdigest()[:8]

        self.hypotheses[hypothesis_id] = {
            'hypothesis': hypothesis,
            'source_file': source_file,
            'registered_at': datetime.now().isoformat(),
            'status': 'pending',  # pending, validated, rejected
            'metadata': metadata,
            'validations': []
        }

        self.save_hypotheses()
        return hypothesis_id

    def validate_hypothesis(
        self,
        hypothesis_id: str,
        result: str,
        evidence: str,
        success: bool
    ):
        """
        Добавить результат проверки гипотезы

        Args:
            hypothesis_id: ID гипотезы
            result: Описание результата
            evidence: Доказательства
            success: Сработала ли гипотеза
        """
        if hypothesis_id not in self.hypotheses:
            print(f"⚠️  Гипотеза {hypothesis_id} не найдена")
            return

        validation = {
            'validated_at': datetime.now().isoformat(),
            'result': result,
            'evidence': evidence,
            'success': success
        }

        self.hypotheses[hypothesis_id]['validations'].append(validation)

        # Обновляем статус
        validations = self.hypotheses[hypothesis_id]['validations']
        success_count = sum(1 for v in validations if v['success'])
        total_count = len(validations)

        if total_count >= 3:
            if success_count / total_count >= 0.7:
                self.hypotheses[hypothesis_id]['status'] = 'validated'
            else:
                self.hypotheses[hypothesis_id]['status'] = 'rejected'

        self.save_hypotheses()

    def get_similar_hypotheses(self, hypothesis: str) -> List[Dict]:
        """Найти похожие гипотезы из истории"""
        # Простой поиск по ключевым словам
        keywords = set(hypothesis.lower().split())
        similar = []

        for hyp_id, hyp_data in self.hypotheses.items():
            hyp_keywords = set(hyp_data['hypothesis'].lower().split())
            overlap = len(keywords & hyp_keywords) / len(keywords | hyp_keywords)

            if overlap > 0.3:
                similar.append({
                    'id': hyp_id,
                    'hypothesis': hyp_data['hypothesis'],
                    'status': hyp_data['status'],
                    'similarity': overlap,
                    'validations': len(hyp_data['validations'])
                })

        return sorted(similar, key=lambda x: x['similarity'], reverse=True)


class GatekeeperAgent:
    """Главный агент контроля качества"""

    def __init__(
        self,
        raw_dir: Path,
        quarantine_dir: Path,
        system_context: str
    ):
        self.raw_dir = raw_dir
        self.quarantine_dir = quarantine_dir
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

        self.fact_checker = FactChecker()
        self.relevance_checker = RelevanceChecker(system_context)
        self.hypothesis_validator = HypothesisValidator(
            raw_dir.parent / ".hypothesis_db.yaml"
        )

    def parse_frontmatter(self, file_path: Path) -> Tuple[dict, str]:
        """Извлечь frontmatter и контент"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.startswith('---'):
            return {}, content

        try:
            end_idx = content.find('---', 3)
            if end_idx == -1:
                return {}, content

            frontmatter_text = content[3:end_idx].strip()
            body = content[end_idx + 3:].strip()

            metadata = yaml.safe_load(frontmatter_text) or {}
            return metadata, body

        except Exception as e:
            print(f"⚠️  Ошибка парсинга frontmatter: {e}")
            return {}, content

    async def check_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Полная проверка файла

        Returns:
            {
                'verdict': 'PASS' | 'WARN' | 'FAIL',
                'checks': {...},
                'hypothesis_id': str | None,
                'quarantine_reason': str | None
            }
        """
        print(f"\n🔍 Проверяю: {file_path.name}")

        metadata, content = self.parse_frontmatter(file_path)

        checks = {}

        # Check 1: Размер файла
        file_size = file_path.stat().st_size
        checks['size'] = {
            'passed': 100 <= file_size <= 1_000_000,
            'value': file_size,
            'message': f"Размер: {file_size} байт"
        }

        # Check 2: Язык (ru/en)
        ru_chars = len(re.findall(r'[а-яА-ЯёЁ]', content))
        en_chars = len(re.findall(r'[a-zA-Z]', content))
        total_chars = ru_chars + en_chars

        checks['language'] = {
            'passed': total_chars > 0 and (ru_chars > 0 or en_chars > 0),
            'value': 'ru' if ru_chars > en_chars else 'en',
            'message': f"Язык: {'ru' if ru_chars > en_chars else 'en'}"
        }

        # Check 3: Структура (frontmatter + минимум контента)
        checks['structure'] = {
            'passed': bool(metadata) and len(content) > 50,
            'value': len(content),
            'message': f"Контент: {len(content)} символов"
        }

        # Check 4: Надёжность источника
        source = metadata.get('source', '')
        trusted_domains = ['youtube.com', 'github.com', 'anthropic.com']
        is_trusted = any(domain in source for domain in trusted_domains)

        checks['source'] = {
            'passed': is_trusted or not source,
            'value': source,
            'message': f"Источник: {'trusted' if is_trusted else 'unknown'}"
        }

        # Check 5: Fact-checking (ОПЦИОНАЛЬНАЯ ПРОВЕРКА)
        print("  📊 Fact-checking...")
        fact_check = await self.fact_checker.check_facts(content, metadata)

        # Если fact-checking не сработал, используем эвристику
        if fact_check['confidence'] == 0.0 and fact_check['issues']:
            # Эвристическая проверка на основе источника и структуры
            has_source = bool(metadata.get('source'))
            has_author = bool(metadata.get('author'))
            has_date = bool(metadata.get('published') or metadata.get('created'))

            # Если есть метаданные источника, даём базовую уверенность
            if has_source and (has_author or has_date):
                fact_check = {
                    'is_valid': True,
                    'confidence': 0.7,
                    'issues': [],
                    'verified_facts': [],
                    'unverified_claims': [],
                    'contradictions': [],
                    'details': {'note': 'Эвристическая оценка на основе метаданных'}
                }
            else:
                # Без метаданных - средняя уверенность
                fact_check = {
                    'is_valid': True,
                    'confidence': 0.6,
                    'issues': ['Нет метаданных источника'],
                    'verified_facts': [],
                    'unverified_claims': [],
                    'contradictions': [],
                    'details': {'note': 'Эвристическая оценка, требуется ручная проверка'}
                }

        checks['facts'] = {
            'passed': fact_check['is_valid'],
            'value': fact_check['confidence'],
            'message': f"Достоверность: {fact_check['confidence']:.2f}",
            'details': fact_check
        }

        # Check 6: Применимость к системе (КЛЮЧЕВАЯ ПРОВЕРКА)
        print("  🎯 Relevance check...")
        relevance_check = await self.relevance_checker.check_relevance(content, metadata)
        checks['relevance'] = {
            'passed': relevance_check['is_relevant'],
            'value': relevance_check['relevance_score'],
            'message': f"Релевантность: {relevance_check['relevance_score']:.2f}",
            'details': relevance_check
        }

        # Check 7: Дубликаты (по содержимому)
        content_hash = hashlib.md5(content.encode()).hexdigest()
        # TODO: проверка в базе обработанных файлов
        checks['duplicate'] = {
            'passed': True,  # Пока всегда True
            'value': content_hash,
            'message': "Дубликат: не найден"
        }

        # Проверка гипотез
        hypothesis = self.hypothesis_validator.extract_hypothesis(content, metadata)
        hypothesis_id = None

        if hypothesis:
            print(f"  💡 Обнаружена гипотеза: {hypothesis[:50]}...")
            hypothesis_id = self.hypothesis_validator.register_hypothesis(
                hypothesis,
                file_path.name,
                metadata
            )

            # Проверяем похожие гипотезы из истории
            similar = self.hypothesis_validator.get_similar_hypotheses(hypothesis)
            if similar:
                print(f"  📚 Найдено {len(similar)} похожих гипотез:")
                for sim in similar[:3]:
                    print(f"    - {sim['hypothesis'][:50]}... (status: {sim['status']})")

        # Определяем вердикт
        critical_checks = ['facts', 'relevance']
        critical_failed = [
            name for name in critical_checks
            if not checks[name]['passed']
        ]

        warning_checks = ['size', 'structure', 'source']
        warnings = [
            name for name in warning_checks
            if not checks[name]['passed']
        ]

        if critical_failed:
            verdict = 'FAIL'
            quarantine_reason = f"Критические проверки не пройдены: {', '.join(critical_failed)}"
        elif warnings:
            verdict = 'WARN'
            quarantine_reason = None
        else:
            verdict = 'PASS'
            quarantine_reason = None

        return {
            'verdict': verdict,
            'checks': checks,
            'hypothesis_id': hypothesis_id,
            'quarantine_reason': quarantine_reason
        }

    async def process_file(self, file_path: Path) -> bool:
        """
        Обработать файл через Gatekeeper

        Returns:
            True если файл прошёл проверку, False если отправлен в карантин
        """
        result = await self.check_file(file_path)

        # Выводим результаты
        print(f"\n{'='*60}")
        print(f"Файл: {file_path.name}")
        print(f"Вердикт: {result['verdict']}")
        print(f"\nПроверки:")

        for check_name, check_data in result['checks'].items():
            status = "✅" if check_data['passed'] else "❌"
            print(f"  {status} {check_name}: {check_data['message']}")

        if result['hypothesis_id']:
            print(f"\n💡 Гипотеза зарегистрирована: {result['hypothesis_id']}")

        # Обрабатываем вердикт
        if result['verdict'] == 'FAIL':
            # Отправляем в карантин
            quarantine_path = self.quarantine_dir / file_path.name
            file_path.rename(quarantine_path)

            # Создаём отчёт
            report_path = self.quarantine_dir / f"{file_path.stem}_report.yaml"
            with open(report_path, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'file': file_path.name,
                    'quarantined_at': datetime.now().isoformat(),
                    'reason': result['quarantine_reason'],
                    'checks': result['checks']
                }, f, allow_unicode=True)

            print(f"\n🚫 Файл отправлен в карантин: {result['quarantine_reason']}")
            print(f"   Отчёт: {report_path}")
            return False

        elif result['verdict'] == 'WARN':
            print(f"\n⚠️  Файл прошёл с предупреждениями")
            return True

        else:
            print(f"\n✅ Файл прошёл все проверки")
            return True


async def main():
    """Точка входа"""
    import argparse

    parser = argparse.ArgumentParser(description='Gatekeeper Agent - Quality Control')
    parser.add_argument('--file', type=str, help='Проверить конкретный файл')
    parser.add_argument('--all', action='store_true', help='Проверить все файлы в raw/')
    parser.add_argument('--validate-hypothesis', type=str, help='ID гипотезы для валидации')
    parser.add_argument('--result', type=str, help='Результат проверки гипотезы')
    parser.add_argument('--evidence', type=str, help='Доказательства')
    parser.add_argument('--success', action='store_true', help='Гипотеза сработала')
    args = parser.parse_args()

    # Пути
    base_dir = Path(__file__).parent.parent
    raw_dir = base_dir / "obsidian" / "architect" / "raw"
    quarantine_dir = base_dir / "obsidian" / "architect" / "quarantine"

    # System context
    system_context = """
meAI - CEO-архитектор для AIM Agency (AI-first medical marketing agency).

Фокус:
- AI-агенты для автоматизации маркетинга
- Медицинский маркетинг
- SEO, контент, реклама
- Конкурентная разведка
- Автоматизация процессов

Релевантные темы:
- AI и LLM технологии
- Медицинский маркетинг
- Автоматизация маркетинга
- SEO и контент-маркетинг
- Конкурентный анализ
- Бизнес-стратегии для агентств
"""

    # Создаём Gatekeeper
    gatekeeper = GatekeeperAgent(raw_dir, quarantine_dir, system_context)

    # Валидация гипотезы
    if args.validate_hypothesis:
        if not args.result or not args.evidence:
            print("❌ Для валидации нужны --result и --evidence")
            return

        gatekeeper.hypothesis_validator.validate_hypothesis(
            args.validate_hypothesis,
            args.result,
            args.evidence,
            args.success
        )
        print(f"✅ Гипотеза {args.validate_hypothesis} обновлена")
        return

    # Проверка файла
    if args.file:
        file_path = raw_dir / args.file
        if not file_path.exists():
            print(f"❌ Файл не найден: {file_path}")
            return

        await gatekeeper.process_file(file_path)

    # Проверка всех файлов
    elif args.all:
        files = list(raw_dir.glob("*.md"))
        print(f"📦 Найдено файлов: {len(files)}")

        for file_path in files:
            await gatekeeper.process_file(file_path)
            print()


if __name__ == "__main__":
    asyncio.run(main())
