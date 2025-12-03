"""
Parsers package for financial statement PDFs.
"""

from parsers.base_parser import BaseStatementParser
from parsers.sunlife_parser import SunLifeParser
from parsers.scotiabank_parser import ScotiaBankParser
from parsers.olympia_parser import OlympiaParser
from parsers.cibc_investorsedge_parser import CIBCInvestorsEdgeParser
from parsers.cibc_pps_parser import CIBCPPSParser

__all__ = [
    'BaseStatementParser',
    'SunLifeParser',
    'ScotiaBankParser',
    'OlympiaParser',
    'CIBCInvestorsEdgeParser',
    'CIBCPPSParser'
]
