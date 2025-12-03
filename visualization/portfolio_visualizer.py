"""
Portfolio visualization module for generating charts and reports.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from analysis.portfolio_analyzer import PortfolioAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class PortfolioVisualizer:
    """Creates visualizations for portfolio analysis."""

    def __init__(self, analyzer: PortfolioAnalyzer):
        """
        Initialize the visualizer.

        Args:
            analyzer: PortfolioAnalyzer instance
        """
        self.analyzer = analyzer

    def plot_asset_allocation(self, output_path: str = None, institution: str = None):
        """
        Create pie chart of current asset allocation.

        Args:
            output_path: Path to save the chart
            institution: Optional institution filter
        """
        df = self.analyzer.get_current_allocation(institution)

        if df.empty:
            logger.warning("No data available for asset allocation chart")
            return

        # Group by asset category
        allocation = df.groupby('asset_category')['total_value'].sum()

        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = sns.color_palette("husl", len(allocation))

        wedges, texts, autotexts = ax.pie(
            allocation.values,
            labels=allocation.index,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )

        # Improve label formatting
        for text in texts:
            text.set_fontsize(12)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)

        title = "Portfolio Asset Allocation"
        if institution:
            title += f" - {institution}"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Asset allocation chart saved to {output_path}")
        else:
            plt.show()

        plt.close()

    def plot_value_trend(self, output_path: str = None, institution: str = None,
                        start_date: datetime = None, end_date: datetime = None):
        """
        Create line chart of portfolio value over time.

        Args:
            output_path: Path to save the chart
            institution: Optional institution filter
            start_date: Optional start date filter
            end_date: Optional end date filter
        """
        df = self.analyzer.get_value_over_time(institution, start_date, end_date)

        if df.empty:
            logger.warning("No data available for value trend chart")
            return

        # Group by date and sum across all accounts
        trend = df.groupby('statement_date')['total_account_value'].sum().reset_index()

        # Create line chart
        fig, ax = plt.subplots(figsize=(14, 6))

        ax.plot(trend['statement_date'], trend['total_account_value'],
               marker='o', linewidth=2, markersize=6, color='#2E86AB')

        # Format axes
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.xticks(rotation=45)

        # Add value labels on points
        for x, y in zip(trend['statement_date'], trend['total_account_value']):
            ax.annotate(f'${y:,.0f}',
                       xy=(x, y),
                       xytext=(0, 10),
                       textcoords='offset points',
                       ha='center',
                       fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))

        # Labels and title
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Portfolio Value ($)', fontsize=12, fontweight='bold')

        title = "Portfolio Value Over Time"
        if institution:
            title += f" - {institution}"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Value trend chart saved to {output_path}")
        else:
            plt.show()

        plt.close()

    def plot_allocation_trend(self, output_path: str = None,
                            start_date: datetime = None, end_date: datetime = None):
        """
        Create stacked area chart of asset allocation over time.

        Args:
            output_path: Path to save the chart
            start_date: Optional start date filter
            end_date: Optional end date filter
        """
        df = self.analyzer.get_asset_allocation_trend(start_date, end_date)

        if df.empty:
            logger.warning("No data available for allocation trend chart")
            return

        # Pivot data for stacked area chart
        pivot = df.pivot_table(
            index='statement_date',
            columns='asset_category',
            values='total_value',
            aggfunc='sum',
            fill_value=0
        )

        # Create stacked area chart
        fig, ax = plt.subplots(figsize=(14, 8))

        # Plot stacked area
        pivot.plot.area(ax=ax, alpha=0.7, linewidth=2)

        # Format axes
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.xticks(rotation=45)

        # Labels and title
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Value ($)', fontsize=12, fontweight='bold')
        ax.set_title('Asset Allocation Evolution Over Time', fontsize=16, fontweight='bold', pad=20)

        ax.legend(title='Asset Category', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Allocation trend chart saved to {output_path}")
        else:
            plt.show()

        plt.close()

    # def plot_allocation_trend(self, output_path: str = None,
    #                         start_date: datetime = None, end_date: datetime = None):
    #     """
    #     Create stacked bar chart of asset allocation over time.
    #     Args:
    #         output_path: Path to save the chart
    #         start_date: Optional start date filter
    #         end_date: Optional end date filter
    #     """
    #     df = self.analyzer.get_asset_allocation_trend(start_date, end_date)
    #     if df.empty:
    #         logger.warning("No data available for allocation trend chart")
    #         return
        
    #     # Pivot data for stacked bar chart
    #     pivot = df.pivot_table(
    #         index='statement_date',
    #         columns='asset_category',
    #         values='total_value',
    #         aggfunc='sum',
    #         fill_value=0
    #     )
        
    #     # Create stacked bar chart
    #     fig, ax = plt.subplots(figsize=(14, 8))
        
    #     # Plot stacked bar chart
    #     pivot.plot.bar(ax=ax, stacked=True, alpha=0.8, width=0.8)
        
    #     # Format axes
    #     ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    #     plt.xticks(rotation=45)
        
    #     # Labels and title
    #     ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    #     ax.set_ylabel('Value ($)', fontsize=12, fontweight='bold')
    #     ax.set_title('Asset Allocation Evolution Over Time', fontsize=16, fontweight='bold', pad=20)
    #     ax.legend(title='Asset Category', bbox_to_anchor=(1.05, 1), loc='upper left')
    #     ax.grid(True, alpha=0.3, axis='y')  # Only show horizontal grid lines for bars
        
    #     plt.tight_layout()
        
    #     if output_path:
    #         plt.savefig(output_path, dpi=300, bbox_inches='tight')
    #         logger.info(f"Allocation trend chart saved to {output_path}")
    #     else:
    #         plt.show()
        
    #     plt.close()

    def plot_allocation_by_account(self, output_path: str = None):
        """
        Create bar chart showing allocation by account.

        Args:
            output_path: Path to save the chart
        """
        df = self.analyzer.get_current_allocation()

        if df.empty:
            logger.warning("No data available for account allocation chart")
            return

        # Create account labels
        df['account_label'] = df['institution_name'] + '\n' + df['account_number']

        # Pivot data
        pivot = df.pivot_table(
            index='account_label',
            columns='asset_category',
            values='total_value',
            aggfunc='sum',
            fill_value=0
        )

        # Create stacked bar chart
        fig, ax = plt.subplots(figsize=(14, 8))

        pivot.plot(kind='bar', stacked=True, ax=ax, width=0.7)

        # Labels and title
        ax.set_xlabel('Account', fontsize=12, fontweight='bold')
        ax.set_ylabel('Value ($)', fontsize=12, fontweight='bold')
        ax.set_title('Asset Allocation by Account', fontsize=16, fontweight='bold', pad=20)

        ax.legend(title='Asset Category', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Account allocation chart saved to {output_path}")
        else:
            plt.show()

        plt.close()

    def plot_top_holdings(self, n: int = 10, output_path: str = None):
        """
        Create bar chart of top N holdings.

        Args:
            n: Number of top holdings to display
            output_path: Path to save the chart
        """
        df = self.analyzer.get_top_holdings(n)

        if df.empty:
            logger.warning("No data available for top holdings chart")
            return

        # Create bar chart
        fig, ax = plt.subplots(figsize=(12, 8))

        colors = sns.color_palette("viridis", len(df))
        bars = ax.barh(df['security_name'], df['market_value'], color=colors)

        # Add value labels
        for i, (bar, value, pct) in enumerate(zip(bars, df['market_value'], df['portfolio_pct'])):
            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2,
                   f'${value:,.0f} ({pct:.1f}%)',
                   ha='left', va='center', fontsize=9, fontweight='bold')

        # Labels and title
        ax.set_xlabel('Market Value ($)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Security', fontsize=12, fontweight='bold')
        ax.set_title(f'Top {n} Holdings by Market Value', fontsize=16, fontweight='bold', pad=20)

        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Top holdings chart saved to {output_path}")
        else:
            plt.show()

        plt.close()

    def plot_returns(self, output_path: str = None, institution: str = None):
        """
        Create line chart of portfolio returns over time.

        Args:
            output_path: Path to save the chart
            institution: Optional institution filter
        """
        df = self.analyzer.calculate_returns(institution)

        if df.empty:
            logger.warning("No data available for returns chart")
            return

        # Group by date for overall portfolio returns
        returns = df.groupby('statement_date').agg({
            'total_account_value': 'sum'
        }).reset_index()

        # Calculate cumulative returns
        returns['cumulative_return'] = (
            (returns['total_account_value'] / returns['total_account_value'].iloc[0] - 1) * 100
        )

        # Create line chart
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Plot 1: Portfolio Value
        ax1.plot(returns['statement_date'], returns['total_account_value'],
                marker='o', linewidth=2, markersize=6, color='#2E86AB')
        ax1.set_ylabel('Portfolio Value ($)', fontsize=12, fontweight='bold')
        ax1.set_title('Portfolio Value and Returns Over Time', fontsize=16, fontweight='bold', pad=20)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Cumulative Returns
        ax2.plot(returns['statement_date'], returns['cumulative_return'],
                marker='o', linewidth=2, markersize=6, color='#A23B72')
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Cumulative Return (%)', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # Format x-axis for both plots
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Returns chart saved to {output_path}")
        else:
            plt.show()

        plt.close()

    def create_dashboard(self, output_dir: str = 'reports'):
        """
        Create a complete dashboard with multiple charts.

        Args:
            output_dir: Directory to save the charts
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        logger.info("Generating portfolio dashboard...")

        # Generate all charts
        self.plot_asset_allocation(f'{output_dir}/asset_allocation_{timestamp}.png')
        self.plot_value_trend(f'{output_dir}/value_trend_{timestamp}.png')
        self.plot_allocation_trend(f'{output_dir}/allocation_trend_{timestamp}.png')
        self.plot_allocation_by_account(f'{output_dir}/allocation_by_account_{timestamp}.png')
        self.plot_top_holdings(output_path=f'{output_dir}/top_holdings_{timestamp}.png')
        self.plot_returns(output_path=f'{output_dir}/returns_{timestamp}.png')

        logger.info(f"Dashboard charts saved to {output_dir}")

        # Generate summary report
        self._generate_summary_report(f'{output_dir}/summary_report_{timestamp}.txt')

    def _generate_summary_report(self, output_path: str):
        """
        Generate text summary report.

        Args:
            output_path: Path to save the report
        """
        summary = self.analyzer.get_portfolio_summary()
        concentration = self.analyzer.get_concentration_risk()
        diversification = self.analyzer.get_diversification_score()

        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("PORTFOLIO SUMMARY REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")

            f.write("PORTFOLIO OVERVIEW\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Portfolio Value: ${summary['total_value']:,.2f}\n")
            f.write(f"Number of Accounts: {summary['num_accounts']}\n")
            f.write(f"Number of Securities: {summary['num_securities']}\n")
            f.write(f"Number of Institutions: {summary['num_institutions']}\n")
            f.write(f"Total Gain/Loss: ${summary['total_gain_loss']:,.2f} ({summary['total_gain_loss_pct']:.2f}%)\n")
            f.write("\n")

            f.write("CONCENTRATION RISK\n")
            f.write("-" * 80 + "\n")
            f.write(f"Top 5 Holdings: {concentration['top5_concentration']:.2f}%\n")
            f.write(f"Top 10 Holdings: {concentration['top10_concentration']:.2f}%\n")
            f.write(f"Largest Asset Category: {concentration['max_category']} ({concentration['max_category_pct']:.2f}%)\n")
            f.write(f"Largest Institution: {concentration['max_institution']} ({concentration['max_institution_pct']:.2f}%)\n")
            f.write("\n")

            f.write("DIVERSIFICATION METRICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Actual Number of Holdings: {diversification['actual_number_holdings']}\n")
            f.write(f"Effective Number of Holdings: {diversification['effective_number_holdings']:.2f}\n")
            f.write(f"Diversification Ratio: {diversification['diversification_ratio']:.2f}\n")
            f.write(f"Number of Asset Categories: {diversification['num_categories']}\n")
            f.write("\n")

        logger.info(f"Summary report saved to {output_path}")
