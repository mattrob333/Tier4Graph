"""
Natural Language Parser Service

Provides an abstraction for parsing natural language vendor queries
into structured MatchingRequest objects.

Architecture:
    - NLParser: Abstract base class defining the parsing interface
    - MockNLParser: Rule-based keyword extraction (no LLM required)
    - Future: OpenAINLParser, AnthropicNLParser (LLM-backed implementations)

Usage:
    parser = get_nl_parser()
    matching_request = await parser.parse("I need HIPAA-compliant colo in US East")
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger

from app.models.matching import MatchingRequest

if TYPE_CHECKING:
    from app.core.config import Settings


class NLParser(ABC):
    """Abstract base class for natural language query parsers.

    Implementations must provide the `parse` method that converts
    a free-form text query into a structured MatchingRequest.
    """

    @abstractmethod
    async def parse(self, query: str) -> MatchingRequest:
        """Parse a natural language query into a structured MatchingRequest.

        Args:
            query: Free-form text describing vendor requirements.

        Returns:
            MatchingRequest with extracted criteria.
        """
        pass


class MockNLParser(NLParser):
    """Rule-based natural language parser using keyword/regex extraction.

    This implementation does not require any LLM API calls. It uses
    simple pattern matching to extract structured criteria from queries.

    Supported extractions:
        - Certifications: HIPAA, SOC 2, ISO 27001, PCI DSS, HITRUST
        - Regions: us-east, us-west, us-central, eu-west, apac
        - Industries: colocation, cloud, managed-services, healthcare, network
        - Services: colocation, interconnection, disaster-recovery, bare-metal
        - Risk tolerance: low (2-3), medium (5), high (7-8)
    """

    # Certification patterns (case-insensitive)
    CERT_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r"\bhipaa\b", re.IGNORECASE), "HIPAA"),
        (re.compile(r"\bsoc\s*2\b", re.IGNORECASE), "SOC 2"),
        (re.compile(r"\bsoc\s*2\s*type\s*(i{1,2}|1|2)\b", re.IGNORECASE), "SOC 2"),
        (re.compile(r"\biso\s*27001\b", re.IGNORECASE), "ISO 27001"),
        (re.compile(r"\bpci[\s-]*dss\b", re.IGNORECASE), "PCI DSS"),
        (re.compile(r"\bpci\s+complian", re.IGNORECASE), "PCI DSS"),
        (re.compile(r"\bhitrust\b", re.IGNORECASE), "HITRUST"),
        (re.compile(r"\bfedramp\b", re.IGNORECASE), "FedRAMP"),
    ]

    # Region patterns
    REGION_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r"\b(us[\s-]?east|east(?:ern)?\s+(?:us|united\s+states)|virginia|ashburn)\b", re.IGNORECASE), "us-east"),
        (re.compile(r"\b(us[\s-]?west|west(?:ern)?\s+(?:us|united\s+states)|california|silicon\s+valley)\b", re.IGNORECASE), "us-west"),
        (re.compile(r"\b(us[\s-]?central|central\s+(?:us|united\s+states)|texas|dallas|chicago)\b", re.IGNORECASE), "us-central"),
        (re.compile(r"\b(eu[\s-]?west|europe|london|uk|ireland|amsterdam)\b", re.IGNORECASE), "eu-west"),
        (re.compile(r"\b(apac|asia|singapore|tokyo|hong\s+kong)\b", re.IGNORECASE), "apac"),
        (re.compile(r"\b(usa|united\s+states|america)\b", re.IGNORECASE), "USA"),
    ]

    # Industry/segment patterns
    INDUSTRY_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r"\b(colo(?:cation)?|data\s+cent(?:er|re))\b", re.IGNORECASE), "colocation"),
        (re.compile(r"\b(cloud|iaas|paas)\b", re.IGNORECASE), "cloud"),
        (re.compile(r"\b(managed[\s-]?(?:service|cloud|hosting))\b", re.IGNORECASE), "managed-cloud"),
        (re.compile(r"\b(health\s*care|medical|hospital|clinical)\b", re.IGNORECASE), "healthcare"),
        (re.compile(r"\b(network|fiber|wavelength|dark\s+fiber)\b", re.IGNORECASE), "network"),
        (re.compile(r"\b(interconnect(?:ion)?|peering|ix)\b", re.IGNORECASE), "interconnection"),
        (re.compile(r"\b(enterprise)\b", re.IGNORECASE), "enterprise"),
        (re.compile(r"\b(edge)\b", re.IGNORECASE), "edge"),
    ]

    # Service patterns
    SERVICE_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r"\b(colo(?:cation)?)\b", re.IGNORECASE), "colocation"),
        (re.compile(r"\b(interconnect(?:ion)?)\b", re.IGNORECASE), "interconnection"),
        (re.compile(r"\b(disaster[\s-]?recovery|dr(?:aas)?|business\s+continuity)\b", re.IGNORECASE), "disaster-recovery"),
        (re.compile(r"\b(bare[\s-]?metal)\b", re.IGNORECASE), "bare-metal"),
        (re.compile(r"\b(managed[\s-]?(?:service|hosting))\b", re.IGNORECASE), "managed-services"),
        (re.compile(r"\b(backup)\b", re.IGNORECASE), "backup"),
        (re.compile(r"\b(hybrid[\s-]?cloud)\b", re.IGNORECASE), "hybrid-cloud"),
    ]

    # Risk tolerance patterns
    RISK_PATTERNS: list[tuple[re.Pattern, int]] = [
        # Very low risk
        (re.compile(r"\b(very\s+low\s+risk|extremely\s+conservative|minimal\s+risk|zero\s+risk)\b", re.IGNORECASE), 1),
        (re.compile(r"\b(low\s+risk|conservative|risk[\s-]?averse|strict\s+(?:compliance|requirements?))\b", re.IGNORECASE), 3),
        # Medium risk
        (re.compile(r"\b(medium\s+risk|moderate\s+risk|balanced|flexible)\b", re.IGNORECASE), 5),
        # High risk tolerance
        (re.compile(r"\b(high(?:er)?\s+risk|aggressive|risk[\s-]?tolerant)\b", re.IGNORECASE), 7),
        (re.compile(r"\b(any\s+risk|doesn'?t?\s+matter|budget|cheap|low[\s-]?cost)\b", re.IGNORECASE), 8),
    ]

    async def parse(self, query: str) -> MatchingRequest:
        """Parse query using keyword/regex extraction.

        Args:
            query: Free-form text describing vendor requirements.

        Returns:
            MatchingRequest with extracted criteria.
        """
        logger.debug(f"MockNLParser parsing query: {query[:100]}...")

        # Extract certifications
        required_certs = self._extract_certs(query)

        # Extract region
        region = self._extract_region(query)

        # Extract industry
        industry = self._extract_industry(query)

        # Extract services
        required_services = self._extract_services(query)

        # Extract risk tolerance
        risk_tolerance = self._extract_risk_tolerance(query)

        result = MatchingRequest(
            industry=industry,
            region=region,
            required_certs=required_certs,
            required_services=required_services,
            risk_tolerance=risk_tolerance,
            text_query=query,
        )

        logger.info(
            f"MockNLParser extracted: industry={industry}, region={region}, "
            f"certs={required_certs}, services={required_services}, risk={risk_tolerance}"
        )

        return result

    def _extract_certs(self, query: str) -> list[str]:
        """Extract certification requirements from query."""
        certs: set[str] = set()
        for pattern, cert_name in self.CERT_PATTERNS:
            if pattern.search(query):
                certs.add(cert_name)
        return sorted(certs)

    def _extract_region(self, query: str) -> str | None:
        """Extract geographic region from query.

        Returns the first matching region (most specific patterns first).
        """
        for pattern, region in self.REGION_PATTERNS:
            if pattern.search(query):
                return region
        return None

    def _extract_industry(self, query: str) -> str | None:
        """Extract industry/segment from query.

        Returns the first matching industry.
        """
        for pattern, industry in self.INDUSTRY_PATTERNS:
            if pattern.search(query):
                return industry
        return None

    def _extract_services(self, query: str) -> list[str]:
        """Extract required services from query."""
        services: set[str] = set()
        for pattern, service in self.SERVICE_PATTERNS:
            if pattern.search(query):
                services.add(service)
        return sorted(services)

    def _extract_risk_tolerance(self, query: str) -> int | None:
        """Extract risk tolerance level from query.

        Returns:
            Integer 1-10 where 1=lowest risk only, 10=any risk acceptable.
            Returns None if no risk preference detected.
        """
        for pattern, tolerance in self.RISK_PATTERNS:
            if pattern.search(query):
                return tolerance
        return None


def get_nl_parser(settings: Settings | None = None) -> NLParser:
    """Factory function to get the appropriate NL parser.

    Currently returns MockNLParser. In the future, this will check
    settings.llm_provider and return the appropriate LLM-backed parser.

    Args:
        settings: Optional Settings instance. If not provided, uses defaults.

    Returns:
        NLParser implementation based on configuration.

    Example future implementation:
        if settings and settings.llm_provider == "openai":
            return OpenAINLParser(api_key=settings.openai_api_key)
        elif settings and settings.llm_provider == "anthropic":
            return AnthropicNLParser(api_key=settings.anthropic_api_key)
        else:
            return MockNLParser()
    """
    # TODO: Add LLM-backed parser selection based on settings.llm_provider
    # For now, always return the mock parser (no API keys required)

    if settings is not None:
        logger.debug(f"get_nl_parser called with llm_provider={getattr(settings, 'llm_provider', None)}")

    # Future: Check settings.llm_provider and instantiate appropriate parser
    # if settings and settings.llm_provider == "openai" and settings.openai_api_key:
    #     from app.services.openai_nl_parser import OpenAINLParser
    #     return OpenAINLParser(api_key=settings.openai_api_key)
    # elif settings and settings.llm_provider == "anthropic" and settings.anthropic_api_key:
    #     from app.services.anthropic_nl_parser import AnthropicNLParser
    #     return AnthropicNLParser(api_key=settings.anthropic_api_key)

    logger.info("Using MockNLParser (no LLM provider configured)")
    return MockNLParser()
