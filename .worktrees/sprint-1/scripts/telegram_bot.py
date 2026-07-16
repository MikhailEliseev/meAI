#!/usr/bin/env python3
"""
Telegram Bot for Architect

Allows you to talk to Architect via Telegram with voice messages.
Uses AssemblyAI for transcription.

Setup:
1. Create bot via @BotFather and get token
2. Set environment variables:
   - TELEGRAM_BOT_TOKEN
   - ASSEMBLYAI_API_KEY
3. Run: python scripts/telegram_bot.py

Usage:
- Send text message with your question
- Send voice message (will be transcribed)
- Use /start to see instructions
- Use /history to see recent decisions
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import assemblyai as aai

from meai.core.architect import Architect, StrategicQuestion


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ArchitectBot:
    """Telegram bot for Architect."""

    def __init__(self):
        """Initialize bot."""
        # Get tokens
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")

        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        if not self.assemblyai_key:
            raise ValueError("ASSEMBLYAI_API_KEY not set")

        # Initialize AssemblyAI
        aai.settings.api_key = self.assemblyai_key

        # Initialize Architect
        self.architect = Architect()

        # Create application
        self.app = Application.builder().token(self.telegram_token).build()

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("history", self.history_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_text = """
👋 Привет! Я Architect - твой стратегический советник для AIM Agency.

**Как пользоваться:**

📝 **Текстом:**
Просто напиши свой вопрос, и я дам стратегическое решение.

🎤 **Голосом:**
Отправь голосовое сообщение - я расшифрую и отвечу.

**Примеры вопросов:**
• Какую нишу выбрать первой?
• Какую цену ставить на SEO-аудит?
• Нужен ли партнёр-разработчик?
• Какой первый агент запустить?

**Команды:**
/help - показать эту справку
/history - последние решения

Задавай любые стратегические вопросы! 🚀
"""
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await self.start_command(update, context)

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command."""
        # Get recent decisions from Obsidian
        decisions_dir = Path("obsidian/architect/decisions")

        if not decisions_dir.exists():
            await update.message.reply_text("📭 Пока нет решений.")
            return

        # Get last 5 decisions
        decisions = sorted(decisions_dir.glob("*.md"), reverse=True)[:5]

        if not decisions:
            await update.message.reply_text("📭 Пока нет решений.")
            return

        history_text = "📚 **Последние решения:**\n\n"

        for i, decision_file in enumerate(decisions, 1):
            # Read file
            content = decision_file.read_text()

            # Extract title
            title = "Без названия"
            for line in content.split('\n'):
                if line.startswith('title:'):
                    title = line.replace('title:', '').strip().strip('"')
                    break

            # Extract date from filename
            date_str = decision_file.stem[:13]  # YYYYMMDD-HHMM

            history_text += f"{i}. {title}\n"
            history_text += f"   📅 {date_str}\n\n"

        await update.message.reply_text(history_text, parse_mode='Markdown')

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text message."""
        question = update.message.text

        # Send "thinking" message
        thinking_msg = await update.message.reply_text("🤔 Думаю...")

        try:
            # Ask Architect
            decision = await self.ask_architect(question)

            # Format response
            response = self.format_decision(decision)

            # Delete thinking message
            await thinking_msg.delete()

            # Send response
            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error handling text: {e}")
            await thinking_msg.edit_text(f"❌ Ошибка: {str(e)}")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice message."""
        # Send "transcribing" message
        status_msg = await update.message.reply_text("🎤 Расшифровываю голосовое...")

        try:
            # Download voice file
            voice_file = await update.message.voice.get_file()
            voice_path = Path(f"/tmp/voice_{update.message.message_id}.ogg")
            await voice_file.download_to_drive(voice_path)

            # Transcribe with AssemblyAI
            await status_msg.edit_text("🎤 Расшифровываю... (это займёт ~10-30 сек)")

            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(str(voice_path))

            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")

            question = transcript.text

            # Show transcribed text
            await status_msg.edit_text(f"📝 Расшифровано:\n_{question}_\n\n🤔 Думаю...", parse_mode='Markdown')

            # Ask Architect
            decision = await self.ask_architect(question)

            # Format response
            response = f"**Вопрос:** {question}\n\n"
            response += self.format_decision(decision)

            # Delete status message
            await status_msg.delete()

            # Send response
            await update.message.reply_text(response, parse_mode='Markdown')

            # Cleanup
            voice_path.unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error handling voice: {e}")
            await status_msg.edit_text(f"❌ Ошибка: {str(e)}")

    async def ask_architect(self, question: str):
        """Ask Architect a question."""
        strategic_q = StrategicQuestion(
            goal=question,
            constraints=[],
            resources={},
            context={}
        )

        decision = await self.architect.make_decision(strategic_q)

        # Save to Obsidian
        await self.save_to_obsidian(question, decision)

        return decision

    async def save_to_obsidian(self, question: str, decision):
        """Save decision to Obsidian."""
        vault_path = Path("obsidian/architect")
        decisions_dir = vault_path / "decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)

        # Create filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
        filename = f"{timestamp}-decision.md"
        filepath = decisions_dir / filename

        # Create content
        content = f"""---
title: "Strategic Decision: {question[:50]}..."
type: strategic-decision
created: {datetime.now(timezone.utc).isoformat()}
confidence: {decision.confidence}
status: active
tags: [decision, strategic, telegram]
---

# Strategic Decision

## Question
{question}

## Decision
{decision.action}

## Rationale
{decision.rationale}

## Confidence
{decision.confidence:.0%}

## Alternatives Considered
"""

        if decision.alternatives:
            for i, alt in enumerate(decision.alternatives, 1):
                content += f"{i}. {alt}\n"
        else:
            content += "None\n"

        content += "\n## Risks\n"

        if decision.risks:
            for risk in decision.risks:
                content += f"- {risk}\n"
        else:
            content += "None identified\n"

        content += f"""
## Metadata
- **Decision ID:** {decision.decision_id}
- **Timestamp:** {decision.timestamp.isoformat()}
- **Source:** Telegram Bot
- **Saved to:** `{filepath.relative_to(vault_path)}`

---

*This decision was made by Architect via Telegram Bot.*
"""

        # Write file
        filepath.write_text(content)

    def format_decision(self, decision) -> str:
        """Format decision for Telegram."""
        response = f"💡 **РЕШЕНИЕ**\n\n"
        response += f"{decision.action}\n\n"
        response += f"**Уверенность:** {decision.confidence:.0%}\n\n"
        response += f"**Обоснование:**\n{decision.rationale[:500]}...\n\n"

        if decision.alternatives:
            response += f"**Альтернативы:**\n"
            for i, alt in enumerate(decision.alternatives[:2], 1):
                response += f"{i}. {alt[:100]}...\n"
            response += "\n"

        if decision.risks:
            response += f"**Риски:**\n"
            for risk in decision.risks[:2]:
                response += f"⚠️ {risk[:100]}...\n"

        response += f"\n✅ Решение сохранено в Obsidian"

        return response

    def run(self):
        """Run the bot."""
        logger.info("Starting Architect Telegram Bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point."""
    try:
        bot = ArchitectBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise


if __name__ == "__main__":
    main()
