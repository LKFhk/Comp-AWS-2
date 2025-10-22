"""
Visualization API endpoints for RiskIntel360 Platform
Provides data visualization endpoints for charts and graphs.
"""

import logging
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import Response
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import io
import base64

from riskintel360.models import data_manager
from riskintel360.auth.auth_decorators import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/visualizations")


@router.get("/{validation_id}/market-analysis")
async def get_market_analysis_chart(
    validation_id: str,
    chart_type: str = "growth_trend",
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Generate market analysis visualization data.
    """
    try:
        # Verify user has access to this validation
        validation = await data_manager.get_validation_request(validation_id)
        if not validation or validation.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get validation result
        result = await data_manager.get_validation_result(validation_id)
        if not result or not result.market_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Market analysis data not found"
            )

        if chart_type == "growth_trend":
            # Market growth trend data
            chart_data = {
                "labels": ["2021", "2022", "2023", "2024", "2025", "2026"],
                "datasets": [
                    {
                        "label": "Market Size ($B)",
                        "data": [1.8, 2.1, 2.5, 2.9, 3.4, 3.9],
                        "borderColor": "rgb(75, 192, 192)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)",
                    }
                ]
            }
        elif chart_type == "segments":
            # Market segments data
            chart_data = {
                "labels": ["Enterprise", "SMB", "Startups", "Government", "Other"],
                "data": [35, 28, 20, 12, 5],
                "backgroundColor": [
                    "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"
                ]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown chart type: {chart_type}"
            )

        return chart_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate market analysis chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate chart data"
        )


@router.get("/{validation_id}/competitive-analysis")
async def get_competitive_analysis_chart(
    validation_id: str,
    chart_type: str = "positioning",
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Generate competitive analysis visualization data.
    """
    try:
        # Verify user has access to this validation
        validation = await data_manager.get_validation_request(validation_id)
        if not validation or validation.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get validation result
        result = await data_manager.get_validation_result(validation_id)
        if not result or not result.competitive_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Competitive analysis data not found"
            )

        if chart_type == "positioning":
            # Competitive positioning scatter plot data
            chart_data = {
                "datasets": [
                    {
                        "label": "Your Business",
                        "data": [{"x": 8.5, "y": 7.2}],
                        "backgroundColor": "rgba(255, 99, 132, 0.8)",
                    },
                    {
                        "label": "Competitor A",
                        "data": [{"x": 6.8, "y": 8.1}],
                        "backgroundColor": "rgba(54, 162, 235, 0.8)",
                    },
                    {
                        "label": "Competitor B",
                        "data": [{"x": 7.5, "y": 6.9}],
                        "backgroundColor": "rgba(255, 206, 86, 0.8)",
                    }
                ]
            }
        elif chart_type == "market_share":
            # Market share data
            chart_data = {
                "labels": ["Competitor A", "Competitor B", "Competitor C", "Others", "Available"],
                "data": [25, 18, 15, 22, 20],
                "backgroundColor": [
                    "rgba(54, 162, 235, 0.8)",
                    "rgba(255, 206, 86, 0.8)",
                    "rgba(75, 192, 192, 0.8)",
                    "rgba(153, 102, 255, 0.8)",
                    "rgba(255, 159, 64, 0.8)"
                ]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown chart type: {chart_type}"
            )

        return chart_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate competitive analysis chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate chart data"
        )


@router.get("/{validation_id}/financial-projections")
async def get_financial_projections_chart(
    validation_id: str,
    chart_type: str = "revenue_profit",
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Generate financial projections visualization data.
    """
    try:
        # Verify user has access to this validation
        validation = await data_manager.get_validation_request(validation_id)
        if not validation or validation.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get validation result
        result = await data_manager.get_validation_result(validation_id)
        if not result or not result.financial_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Financial analysis data not found"
            )

        if chart_type == "revenue_profit":
            # Revenue and profit projections
            chart_data = {
                "labels": ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"],
                "datasets": [
                    {
                        "label": "Revenue ($K)",
                        "data": [250, 580, 920, 1350, 1850],
                        "borderColor": "rgb(75, 192, 192)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)",
                    },
                    {
                        "label": "Profit ($K)",
                        "data": [-150, 120, 380, 650, 980],
                        "borderColor": "rgb(255, 99, 132)",
                        "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    }
                ]
            }
        elif chart_type == "cost_breakdown":
            # Cost breakdown data
            chart_data = {
                "labels": ["Personnel", "Marketing", "Operations", "R&D", "Infrastructure", "Other"],
                "datasets": [
                    {
                        "label": "Year 1 Costs ($K)",
                        "data": [180, 85, 45, 60, 35, 25],
                        "backgroundColor": "rgba(54, 162, 235, 0.8)",
                    },
                    {
                        "label": "Year 3 Costs ($K)",
                        "data": [320, 150, 85, 110, 65, 45],
                        "backgroundColor": "rgba(255, 99, 132, 0.8)",
                    }
                ]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown chart type: {chart_type}"
            )

        return chart_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate financial projections chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate chart data"
        )


@router.get("/{validation_id}/plotly/{chart_type}")
async def get_plotly_chart(
    validation_id: str,
    chart_type: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Generate interactive Plotly charts for validation results.
    """
    try:
        # Verify user has access to this validation
        validation = await data_manager.get_validation_request(validation_id)
        if not validation or validation.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get validation result
        result = await data_manager.get_validation_result(validation_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation result not found"
            )

        if chart_type == "market_growth":
            # Create market growth trend chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=["2021", "2022", "2023", "2024", "2025", "2026"],
                y=[1.8, 2.1, 2.5, 2.9, 3.4, 3.9],
                mode='lines+markers',
                name='Market Size ($B)',
                line=dict(color='rgb(75, 192, 192)', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Market Growth Trend",
                xaxis_title="Year",
                yaxis_title="Market Size (Billions USD)",
                hovermode='x unified'
            )

        elif chart_type == "competitive_positioning":
            # Create competitive positioning scatter plot
            fig = go.Figure()
            
            competitors = [
                {"name": "Your Business", "x": 8.5, "y": 7.2, "color": "red"},
                {"name": "Competitor A", "x": 6.8, "y": 8.1, "color": "blue"},
                {"name": "Competitor B", "x": 7.5, "y": 6.9, "color": "green"},
                {"name": "Competitor C", "x": 5.2, "y": 7.8, "color": "orange"}
            ]
            
            for comp in competitors:
                fig.add_trace(go.Scatter(
                    x=[comp["x"]],
                    y=[comp["y"]],
                    mode='markers',
                    name=comp["name"],
                    marker=dict(size=15, color=comp["color"]),
                    text=comp["name"],
                    textposition="top center"
                ))
            
            fig.update_layout(
                title="Competitive Positioning Map",
                xaxis_title="Innovation Score",
                yaxis_title="Market Presence",
                xaxis=dict(range=[0, 10]),
                yaxis=dict(range=[0, 10])
            )

        elif chart_type == "financial_projections":
            # Create financial projections chart
            fig = go.Figure()
            
            years = ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"]
            revenue = [250, 580, 920, 1350, 1850]
            profit = [-150, 120, 380, 650, 980]
            
            fig.add_trace(go.Scatter(
                x=years,
                y=revenue,
                mode='lines+markers',
                name='Revenue ($K)',
                line=dict(color='rgb(75, 192, 192)', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=years,
                y=profit,
                mode='lines+markers',
                name='Profit ($K)',
                line=dict(color='rgb(255, 99, 132)', width=3)
            ))
            
            fig.update_layout(
                title="Revenue & Profit Projections",
                xaxis_title="Time Period",
                yaxis_title="Amount (Thousands USD)",
                hovermode='x unified'
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown chart type: {chart_type}"
            )

        # Convert to JSON
        chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
        
        return Response(
            content=chart_json,
            media_type="application/json"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate Plotly chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate chart"
        )


@router.get("/{validation_id}/matplotlib/{chart_type}")
async def get_matplotlib_chart(
    validation_id: str,
    chart_type: str,
    format: str = "png",
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Generate static matplotlib charts for validation results.
    """
    try:
        # Verify user has access to this validation
        validation = await data_manager.get_validation_request(validation_id)
        if not validation or validation.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get validation result
        result = await data_manager.get_validation_result(validation_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation result not found"
            )

        # Create matplotlib figure
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_type == "market_segments":
            # Market segments pie chart
            labels = ["Enterprise", "SMB", "Startups", "Government", "Other"]
            sizes = [35, 28, 20, 12, 5]
            colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('Market Segments Distribution')

        elif chart_type == "risk_matrix":
            # Risk assessment matrix
            risks = [
                {"name": "Market Risk", "probability": 6, "impact": 7},
                {"name": "Financial Risk", "probability": 4, "impact": 8},
                {"name": "Operational Risk", "probability": 5, "impact": 5},
                {"name": "Technology Risk", "probability": 7, "impact": 6},
                {"name": "Regulatory Risk", "probability": 3, "impact": 9}
            ]
            
            for risk in risks:
                ax.scatter(risk["probability"], risk["impact"], s=100, alpha=0.7)
                ax.annotate(risk["name"], (risk["probability"], risk["impact"]), 
                           xytext=(5, 5), textcoords='offset points')
            
            ax.set_xlabel('Probability (1-10)')
            ax.set_ylabel('Impact (1-10)')
            ax.set_title('Risk Assessment Matrix')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown chart type: {chart_type}"
            )

        # Save to bytes buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format=format, dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)

        # Return image
        media_type = f"image/{format}"
        return Response(
            content=img_buffer.getvalue(),
            media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate matplotlib chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate chart"
        )


@router.get("/{validation_id}/dashboard-data")
async def get_dashboard_data(
    validation_id: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Get comprehensive dashboard data for a validation result.
    """
    try:
        # Verify user has access to this validation
        validation = await data_manager.get_validation_request(validation_id)
        if not validation or validation.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get validation result
        result = await data_manager.get_validation_result(validation_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation result not found"
            )

        # Compile dashboard data
        dashboard_data = {
            "overall_score": result.overall_score,
            "confidence_level": result.confidence_level,
            "completion_time": result.completion_time_seconds,
            "generated_at": result.generated_at.isoformat() if result.generated_at else None,
            
            "market_insights": {
                "market_size": "$2.5B",
                "growth_rate": "15% CAGR",
                "maturity": "Growing",
                "opportunity_score": 8.2
            },
            
            "competitive_insights": {
                "direct_competitors": 3,
                "market_leader_share": 25,
                "differentiation_score": "High",
                "competitive_intensity": "Medium"
            },
            
            "financial_insights": {
                "initial_investment": "$500K",
                "break_even": "18 months",
                "roi_3_year": "250%",
                "revenue_projection_y3": "$920K"
            },
            
            "risk_insights": {
                "overall_risk": "Medium",
                "market_risk": "Medium",
                "financial_risk": "Low",
                "operational_risk": "Low"
            },
            
            "customer_insights": {
                "target_segments": 3,
                "market_demand": "High",
                "satisfaction_score": 4.2,
                "acquisition_channels": ["Organic Search", "Paid Advertising", "Referrals"]
            },
            
            "recommendations_count": len(result.strategic_recommendations) if result.strategic_recommendations else 0
        }

        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard data"
        )
