"""
Analysis tools for various calculations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnalysisTools:
    """Tools for financial analysis and calculations."""
    
    @staticmethod
    def calculate_capital_gains(book_value: float, market_value: float) -> Dict[str, float]:
        """
        Calculate capital gains/losses.
        
        Args:
            book_value: Original purchase cost
            market_value: Current market value
            
        Returns:
            Dictionary with gain_loss and gain_loss_pct
        """
        gain_loss = market_value - book_value
        gain_loss_pct = (gain_loss / book_value * 100) if book_value > 0 else 0
        
        return {
            "gain_loss": float(gain_loss),
            "gain_loss_pct": float(gain_loss_pct)
        }
    
    @staticmethod
    def calculate_tax_on_capital_gain(gain: float, inclusion_rate: float = 0.5,
                                     tax_rate: float = 0.30) -> float:
        """
        Calculate tax on capital gain (Canadian tax system).
        
        Args:
            gain: Capital gain amount
            inclusion_rate: Capital gains inclusion rate (default 50% for Canada)
            tax_rate: Marginal tax rate
            
        Returns:
            Tax amount
        """
        taxable_gain = gain * inclusion_rate
        tax = taxable_gain * tax_rate
        return float(tax)
    
    @staticmethod
    def calculate_portfolio_metrics(holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate portfolio-level metrics.
        
        Args:
            holdings: List of holding dictionaries
            
        Returns:
            Dictionary with portfolio metrics
        """
        if not holdings:
            return {}
        
        df = pd.DataFrame(holdings)
        
        # Ensure market_value is numeric
        if 'market_value' in df.columns:
            df['market_value'] = pd.to_numeric(df['market_value'], errors='coerce').fillna(0)
        
        total_value = df['market_value'].sum() if 'market_value' in df.columns else 0
        
        metrics = {
            "total_value": float(total_value),
            "num_holdings": len(df),
            "avg_position_size": float(total_value / len(df)) if len(df) > 0 else 0
        }
        
        # Calculate by asset category if available
        if 'asset_category' in df.columns:
            category_totals = df.groupby('asset_category')['market_value'].sum()
            metrics['by_category'] = {
                cat: float(val) for cat, val in category_totals.items()
            }
            metrics['by_category_pct'] = {
                cat: float((val / total_value * 100) if total_value > 0 else 0)
                for cat, val in category_totals.items()
            }
        
        return metrics
    
    @staticmethod
    def identify_tax_loss_harvesting(holdings: List[Dict[str, Any]],
                                    min_loss: float = 100.0) -> List[Dict[str, Any]]:
        """
        Identify tax loss harvesting opportunities.
        
        Args:
            holdings: List of holding dictionaries
            min_loss: Minimum loss amount to consider
            
        Returns:
            List of tax loss harvesting opportunities
        """
        opportunities = []
        
        for holding in holdings:
            # Handle None values safely
            book_value_raw = holding.get('book_value')
            market_value_raw = holding.get('market_value')
            
            try:
                book_value = float(book_value_raw) if book_value_raw is not None else 0.0
            except (ValueError, TypeError):
                book_value = 0.0
            
            try:
                market_value = float(market_value_raw) if market_value_raw is not None else 0.0
            except (ValueError, TypeError):
                market_value = 0.0
            
            if book_value > market_value and book_value > 0:  # Unrealized loss
                loss = book_value - market_value
                if loss >= min_loss:
                    # Estimate tax benefit (50% inclusion, assume 30% tax rate)
                    tax_benefit = loss * 0.5 * 0.30
                    
                    opportunities.append({
                        "security": holding.get('security_name') or 'Unknown',
                        "symbol": holding.get('symbol') or '',
                        "unrealized_loss": float(loss),
                        "tax_benefit": float(tax_benefit),
                        "account": holding.get('account_number') or '',
                        "institution": holding.get('institution_name') or ''
                    })
        
        # Sort by tax benefit (descending)
        opportunities.sort(key=lambda x: x['tax_benefit'], reverse=True)
        
        return opportunities
    
    @staticmethod
    def calculate_probate_fees(estate_value: float, province: str = "ON") -> float:
        """
        Calculate probate fees by province (Ontario rates as default).
        
        Args:
            estate_value: Total estate value
            province: Province code
            
        Returns:
            Probate fee amount
        """
        # Ontario probate fees (2024 rates)
        if province.upper() == "ON":
            if estate_value <= 50000:
                return 0
            elif estate_value <= 1000000:
                return 5.00 + ((estate_value - 50000) * 0.0015)
            else:
                return 15000.00 + ((estate_value - 1000000) * 0.0015)
        
        # Default to Ontario rates if province not specified
        return AnalysisTools.calculate_probate_fees(estate_value, "ON")
    
    @staticmethod
    def recommend_withdrawal_order(accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Recommend optimal withdrawal order for tax efficiency.
        
        Args:
            accounts: List of account dictionaries with type and balance
            
        Returns:
            Ordered list of withdrawal recommendations
        """
        # Priority: TFSA (tax-free) > Non-registered (capital gains) > RRSP (fully taxable)
        priority_map = {
            "TFSA": 1,
            "Non-Registered": 2,
            "RRSP": 3,
            "LIRA": 4,
            "RRIF": 3  # Similar to RRSP
        }
        
        recommendations = []
        for account in accounts:
            account_type = account.get('account_type', 'Unknown')
            priority = priority_map.get(account_type, 5)
            
            recommendations.append({
                "account": account.get('account_number', ''),
                "account_type": account_type,
                "institution": account.get('institution_name', ''),
                "balance": account.get('balance', 0),
                "priority": priority,
                "rationale": _get_withdrawal_rationale(account_type)
            })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'])
        
        return recommendations


def _get_withdrawal_rationale(account_type: str) -> str:
    """Get rationale for withdrawal order based on account type."""
    rationales = {
        "TFSA": "Tax-free withdrawals, no impact on taxable income",
        "Non-Registered": "Only capital gains taxed at 50% inclusion rate",
        "RRSP": "Fully taxable as income, defer if possible",
        "LIRA": "Restricted access, consult regulations",
        "RRIF": "Minimum withdrawals required, fully taxable"
    }
    return rationales.get(account_type, "Consider tax implications")

