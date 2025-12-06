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

import json
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger
from openai import AsyncOpenAI

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


class OpenAINLParser(NLParser):
    """LLM-backed NL parser using OpenAI Chat Completions API.

    Uses gpt-4o to extract structured criteria from natural language
    vendor requirement queries. Falls back to MockNLParser on any error.
    """

    SYSTEM_PROMPT = """You are an expert query parser for an IT infrastructure procurement system. Extract structured criteria from natural language vendor requirement queries with high precision.

CONTEXT: Users search for IT vendors in a Neo4j graph database containing:
- Vendors with segments: colocation, cloud, network, managed-services, security, backup-dr, edge, interconnection
- Facilities with geo regions: us-east, us-west, us-central, eu-west, eu-central, apac
- Services: colocation, wavelengths, dark-fiber, interconnection, disaster-recovery, bare-metal, backup, immutable-backup, DRaaS
- Certifications: SOC 2, HIPAA, ISO 27001, PCI DSS, HITRUST, FedRAMP

Return a JSON object:
{
  "industry": string or null - Vendor segment. CRITICAL MAPPINGS:
    - "backup", "disaster recovery", "DR", "backup & disaster-recovery" → "backup-dr"
    - "network provider", "carrier", "wavelength", "fiber" → "network"
    - "data center", "colocation", "colo" → "colocation"
    - "cloud provider", "IaaS", "PaaS" → "cloud"
    - "security", "SIEM", "MDR", "SOC" → "security"
  
  "regions": array of strings - Geographic REGIONS mentioned (NOT cities). Normalize to:
    - "US-West", "West Coast", "California" → "us-west"
    - "US-East", "East Coast", "Virginia", "Ashburn" → "us-east"
    - "US-Central", "Texas", "Dallas", "Chicago" → "us-central"
    - "EU-West", "London", "Ireland", "Amsterdam" → "eu-west"
    - "EU-Central", "Frankfurt", "Germany" → "eu-central"
    - "APAC", "Asia", "Singapore", "Tokyo" → "apac"
  
  "cities": array of strings - SPECIFIC city names only if mentioned as cities (not regions)
  
  "required_certs": array of strings - Normalize: "SOC 2", "HIPAA", "ISO 27001", "PCI DSS", "HITRUST", "FedRAMP"
  
  "required_services": array of strings - Service keywords. CRITICAL MAPPINGS:
    - "immutable copies", "immutable backup" → "immutable"
    - "RTO", "recovery time" → "disaster-recovery"
    - "wavelength", "waves", "optical" → "wavelength"
    - "backup", "data protection" → "backup"
    - "DRaaS", "disaster recovery as a service" → "DRaaS"
  
  "risk_tolerance": integer 1-10 or null - 1=very conservative, 3=low, 5=moderate, 10=any
  
  "max_risk_score": number or null - EXACT threshold if specified like "≤ 0.25" or "below 0.25" (0.0-1.0 scale)
  
  "result_limit": integer or null - If user says "top 2", "top five", "best 3" etc., extract that number
  
  "sort_by": string or null - If user specifies sort order:
    - "lowest risk first", "by risk ascending" → "risk_asc"
    - "highest score", "best match" → "score_desc" (default)
    - "alphabetical" → "name_asc"
}

EXAMPLES:

Query: "I need a backup & disaster-recovery vendor that can guarantee a 4-hour RTO, keeps immutable copies in both US-West and EU-Central, carries ISO-27001, and has a risk_level_guess below 0.25. Return only the top two, ranked by lowest risk first."
→ {"industry": "backup-dr", "regions": ["us-west", "eu-central"], "cities": [], "required_certs": ["ISO 27001"], "required_services": ["disaster-recovery", "immutable"], "risk_tolerance": null, "max_risk_score": 0.25, "result_limit": 2, "sort_by": "risk_asc"}

Query: "Find network providers with 10 Gbps waves between Chicago and Dallas, SOC 2 certified, risk ≤ 0.25"
→ {"industry": "network", "regions": [], "cities": ["Chicago", "Dallas"], "required_certs": ["SOC 2"], "required_services": ["wavelength"], "risk_tolerance": null, "max_risk_score": 0.25, "result_limit": null, "sort_by": null}

Query: "Healthcare HIPAA-compliant colocation in US East, low risk, top 5 results"
→ {"industry": "colocation", "regions": ["us-east"], "cities": [], "required_certs": ["HIPAA"], "required_services": ["colocation"], "risk_tolerance": 3, "max_risk_score": null, "result_limit": 5, "sort_by": null}

RULES:
- "backup & disaster-recovery" or "DR vendor" → industry: "backup-dr" (CRITICAL!)
- Extract REGIONS (us-west, eu-central) separately from CITIES (Chicago, Dallas)
- "below 0.25" or "< 0.25" or "≤ 0.25" → max_risk_score: 0.25
- "top two" or "top 2" → result_limit: 2
- "lowest risk first" → sort_by: "risk_asc"
- Return ONLY valid JSON"""

    def __init__(self, api_key: str):
        """Initialize the OpenAI parser.

        Args:
            api_key: OpenAI API key for authentication.
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self._fallback = MockNLParser()

    async def parse(self, query: str) -> MatchingRequest:
        """Parse query using OpenAI Chat Completions API.

        Args:
            query: Free-form text describing vendor requirements.

        Returns:
            MatchingRequest with extracted criteria.
            Falls back to MockNLParser on any error.
        """
        logger.debug(f"OpenAINLParser parsing query: {query[:100]}...")

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # Upgraded from gpt-4o-mini for better extraction
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"Parse this query:\n\n{query}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=512,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            data = json.loads(content)
            logger.info(f"OpenAI parsed response: {json.dumps(data, indent=2)}")

            result = MatchingRequest(
                industry=data.get("industry"),
                region=data.get("region"),
                regions=data.get("regions", []),
                required_certs=data.get("required_certs", []),
                required_services=data.get("required_services", []),
                risk_tolerance=data.get("risk_tolerance"),
                max_risk_score=data.get("max_risk_score"),
                cities=data.get("cities", []),
                result_limit=data.get("result_limit"),
                sort_by=data.get("sort_by"),
                text_query=query,
            )

            logger.info(
                f"OpenAINLParser extracted: industry={result.industry}, regions={result.regions}, "
                f"cities={result.cities}, certs={result.required_certs}, services={result.required_services}, "
                f"max_risk_score={result.max_risk_score}, limit={result.result_limit}, sort={result.sort_by}"
            )
            return result

        except Exception as e:
            logger.error(f"OpenAI parsing failed, falling back to MockNLParser: {e}")
            return await self._fallback.parse(query)


def get_nl_parser(settings: Settings | None = None) -> NLParser:
    """Factory function to get the appropriate NL parser.

    Selects parser based on settings.llm_provider:
    - "openai" + api_key: Uses OpenAINLParser (gpt-4o-mini)
    - Otherwise: Uses MockNLParser (keyword extraction)

    Args:
        settings: Optional Settings instance. If not provided, uses MockNLParser.

    Returns:
        NLParser implementation based on configuration.
    """
    if settings is not None:
        logger.debug(f"get_nl_parser called with llm_provider={settings.llm_provider}")

        if settings.llm_provider == "openai" and settings.openai_api_key:
            logger.info("Using OpenAINLParser")
            return OpenAINLParser(api_key=settings.openai_api_key)

    logger.info("Using MockNLParser (no LLM provider configured)")
    return MockNLParser()
