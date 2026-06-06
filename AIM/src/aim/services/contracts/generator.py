"""
Contract Generator

Generates PDF contracts from templates with Russian font support.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import structlog
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT

from src.aim.services.contracts.templates import (
    ContractTemplate,
    ContractType,
    fill_template,
)

logger = structlog.get_logger()


class ContractGenerator:
    """
    Contract PDF generator with Russian font support

    Generates professional PDF contracts from templates.
    """

    def __init__(self, output_dir: str = "./data/contracts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.contract_counter = 0  # Counter for contract numbers
        # Using standard Helvetica - no font registration needed

    def _register_fonts(self) -> None:
        """Font registration removed - using standard Helvetica"""
        pass

    def generate_contract(
        self,
        contract_type: ContractType,
        client_data: Dict[str, Any],
        contract_data: Dict[str, Any],
    ) -> str:
        """
        Generate PDF contract

        Args:
            contract_type: Type of contract
            client_data: Client information
            contract_data: Contract-specific data

        Returns:
            Path to generated PDF file
        """
        # Get template
        template = ContractTemplate(contract_type)
        template_text = template.get_template()

        # Fill template
        filled_text = fill_template(template_text, client_data, contract_data)

        # Generate PDF
        contract_number = contract_data.get("contract_number", "DRAFT")
        filename = f"{contract_type.value}_{contract_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
        output_path = self.output_dir / filename

        self._create_pdf(filled_text, str(output_path), contract_data)

        logger.info(
            "contract_generated",
            contract_type=contract_type,
            contract_number=contract_number,
            output_path=str(output_path),
        )

        return str(output_path)

    def _create_pdf(
        self,
        text: str,
        output_path: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Create PDF from text"""
        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=f"Договор №{metadata.get('contract_number', 'DRAFT')}",
            author="AIM Agency",
        )

        # Create styles
        styles = self._create_styles()

        # Build content
        story = []

        # Split text into paragraphs
        paragraphs = text.strip().split("\n\n")

        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            # Determine style based on content
            if para_text.startswith("ДОГОВОР") or para_text.startswith("СОГЛАШЕНИЕ"):
                style = styles["Title"]
            elif para_text.startswith("ПРИЛОЖЕНИЕ"):
                story.append(PageBreak())
                style = styles["Heading1"]
            elif any(para_text.startswith(f"{i}.") for i in range(1, 11)):
                style = styles["Heading1"]
            elif any(para_text.startswith(f"{i}.{j}") for i in range(1, 11) for j in range(1, 11)):
                style = styles["Heading2"]
            elif "ИСПОЛНИТЕЛЬ:" in para_text or "ЗАКАЗЧИК:" in para_text:
                style = styles["Signature"]
            else:
                style = styles["Normal"]

            # Create paragraph
            para = Paragraph(para_text, style)
            story.append(para)
            story.append(Spacer(1, 0.3 * cm))

        # Build PDF
        doc.build(story)

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create paragraph styles"""
        styles = getSampleStyleSheet()

        # Use Helvetica (standard font with Cyrillic support)
        # Override existing styles instead of adding duplicates
        styles["Normal"].fontName = "Helvetica"
        styles["Normal"].fontSize = 11
        styles["Normal"].leading = 14
        styles["Normal"].alignment = TA_JUSTIFY
        styles["Normal"].spaceAfter = 6

        styles["Title"].fontName = "Helvetica-Bold"
        styles["Title"].fontSize = 14
        styles["Title"].leading = 18
        styles["Title"].alignment = TA_CENTER
        styles["Title"].spaceAfter = 12

        styles["Heading1"].fontName = "Helvetica-Bold"
        styles["Heading1"].fontSize = 12
        styles["Heading1"].leading = 16
        styles["Heading1"].spaceAfter = 8

        styles["Heading2"].fontName = "Helvetica"
        styles["Heading2"].fontSize = 11
        styles["Heading2"].leading = 14
        styles["Heading2"].spaceAfter = 6
        styles["Heading2"].leftIndent = 0.5 * cm

        # Add custom Signature style (only this one is new)
        styles.add(
            ParagraphStyle(
                name="Signature",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=13,
                spaceAfter=4,
            )
        )

        return styles

    def generate_service_agreement(
        self,
        client_data: Dict[str, Any],
        pricing: Dict[str, Any],
    ) -> str:
        """
        Generate service agreement

        Args:
            client_data: Client information (name, INN, address, etc.)
            pricing: Pricing information (monthly_fee, ad_budget, etc.)

        Returns:
            Path to generated PDF
        """
        # Generate contract number
        contract_number = self._generate_contract_number()

        # Prepare contract data
        contract_data = {
            "contract_number": contract_number,
            "contract_date": datetime.now().strftime("%d.%m.%Y"),
            "contract_end_date": (datetime.now() + timedelta(days=365)).strftime("%d.%m.%Y"),
            "city": "Москва",
            **pricing,
        }

        return self.generate_contract(
            ContractType.SERVICE_AGREEMENT,
            client_data,
            contract_data,
        )

    def generate_nda(
        self,
        client_data: Dict[str, Any],
    ) -> str:
        """
        Generate NDA

        Args:
            client_data: Client information

        Returns:
            Path to generated PDF
        """
        contract_number = self._generate_contract_number("NDA")

        contract_data = {
            "contract_number": contract_number,
            "contract_date": datetime.now().strftime("%d.%m.%Y"),
            "city": "Москва",
        }

        return self.generate_contract(
            ContractType.NDA,
            client_data,
            contract_data,
        )

    def generate_addendum(
        self,
        client_data: Dict[str, Any],
        original_contract_number: str,
        original_contract_date: str,
        changes: str,
    ) -> str:
        """
        Generate addendum to existing contract

        Args:
            client_data: Client information
            original_contract_number: Original contract number
            original_contract_date: Original contract date
            changes: Description of changes

        Returns:
            Path to generated PDF
        """
        addendum_number = self._generate_addendum_number(original_contract_number)

        contract_data = {
            "contract_number": original_contract_number,
            "contract_date": original_contract_date,
            "addendum_number": addendum_number,
            "addendum_date": datetime.now().strftime("%d.%m.%Y"),
            "addendum_changes": changes,
            "city": "Москва",
        }

        return self.generate_contract(
            ContractType.ADDENDUM,
            client_data,
            contract_data,
        )

    def _generate_contract_number(self, prefix: str = "AIM") -> str:
        """Generate unique contract number"""
        # Format: AIM-YYYY-NNN
        year = datetime.now().year

        # Increment counter
        self.contract_counter += 1

        return f"{prefix}-{year}-{self.contract_counter:03d}"

    def _generate_addendum_number(self, contract_number: str) -> str:
        """Generate addendum number for contract"""
        # Count existing addendums for this contract
        pattern = f"addendum_{contract_number}_*"
        existing = list(self.output_dir.glob(pattern))
        next_number = len(existing) + 1

        return str(next_number)


class ContractVersioning:
    """
    Contract version management

    Tracks contract versions and changes.
    """

    def __init__(self, storage_dir: str = "./data/contracts/versions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_version(
        self,
        contract_number: str,
        version: int,
        file_path: str,
        changes: Optional[str] = None,
    ) -> None:
        """Save contract version"""
        version_data = {
            "contract_number": contract_number,
            "version": version,
            "file_path": file_path,
            "created_at": datetime.now().isoformat(),
            "changes": changes,
        }

        # Save version metadata
        version_file = self.storage_dir / f"{contract_number}_v{version}.json"
        import json
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(version_data, f, ensure_ascii=False, indent=2)

        logger.info(
            "contract_version_saved",
            contract_number=contract_number,
            version=version,
        )

    def get_latest_version(self, contract_number: str) -> Optional[int]:
        """Get latest version number for contract"""
        pattern = f"{contract_number}_v*.json"
        versions = list(self.storage_dir.glob(pattern))

        if not versions:
            return None

        # Extract version numbers
        version_numbers = []
        for v in versions:
            try:
                version_str = v.stem.split("_v")[1]
                version_numbers.append(int(version_str))
            except (IndexError, ValueError):
                continue

        return max(version_numbers) if version_numbers else None

    def get_version_history(self, contract_number: str) -> list:
        """Get version history for contract"""
        pattern = f"{contract_number}_v*.json"
        versions = list(self.storage_dir.glob(pattern))

        history = []
        import json
        for version_file in sorted(versions):
            with open(version_file, "r", encoding="utf-8") as f:
                history.append(json.load(f))

        return history
