"""Comprehensive chart generation for GitHub stats visualization."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy.orm import Session

from ..models.interactions import Interaction, InteractionType


class ChartGenerator:
    """Generate various chart types for GitHub interaction data."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_interactions_data(self, filters: dict | None = None) -> pd.DataFrame:
        """Get interactions data as DataFrame with optional filters."""
        query = self.db.query(Interaction)

        if filters:
            if filters.get("start_date"):
                query = query.filter(Interaction.timestamp >= filters["start_date"])
            if filters.get("end_date"):
                query = query.filter(Interaction.timestamp <= filters["end_date"])
            if filters.get("interaction_types"):
                query = query.filter(Interaction.type.in_(filters["interaction_types"]))
            if filters.get("repositories"):
                query = query.filter(
                    Interaction.repository_id.in_(filters["repositories"])
                )
            if filters.get("organizations"):
                query = query.filter(
                    Interaction.organization_id.in_(filters["organizations"])
                )
            if not filters.get("include_stars", True):  # Default to include stars
                query = query.filter(Interaction.type != InteractionType.STAR)

        interactions = query.all()

        data = []
        for interaction in interactions:
            data.append(
                {
                    "id": interaction.id,
                    "type": interaction.type.value,
                    "timestamp": interaction.timestamp,
                    "user": interaction.user,
                    "action": interaction.action,
                    "repository_id": interaction.repository_id,
                    "organization_id": interaction.organization_id,
                    "repository_name": interaction.repository.full_name
                    if interaction.repository
                    else None,
                    "organization_name": interaction.organization.name
                    if interaction.organization
                    else None,
                    "date": interaction.timestamp.date(),
                    "hour": interaction.timestamp.hour,
                    "day_of_week": interaction.timestamp.strftime("%A"),
                    "week": interaction.timestamp.strftime("%Y-W%U"),
                    "month": interaction.timestamp.strftime("%Y-%m"),
                }
            )

        return pd.DataFrame(data)

    def create_time_series_chart(
        self, df: pd.DataFrame, groupby: str = "date"
    ) -> go.Figure:
        """Create time series line chart showing interactions over time by type."""
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
            return fig

        # Group by time period and interaction type
        time_series = df.groupby([groupby, "type"]).size().reset_index(name="count")

        fig = px.line(
            time_series,
            x=groupby,
            y="count",
            color="type",
            title=f"GitHub Interactions Over Time (by {groupby})",
            labels={"count": "Number of Interactions", groupby: groupby.title()},
        )

        fig.update_layout(
            xaxis_title=groupby.title(),
            yaxis_title="Number of Interactions",
            legend_title="Interaction Type",
            hovermode="x unified",
        )

        return fig

    def create_stacked_bar_chart(
        self, df: pd.DataFrame, groupby: str = "date"
    ) -> go.Figure:
        """Create stacked bar chart showing interaction types by time period."""
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
            return fig

        # Group by time period and interaction type
        stacked_data = df.groupby([groupby, "type"]).size().reset_index(name="count")

        fig = px.bar(
            stacked_data,
            x=groupby,
            y="count",
            color="type",
            title=f"GitHub Interactions Breakdown (by {groupby})",
            labels={"count": "Number of Interactions", groupby: groupby.title()},
        )

        fig.update_layout(
            xaxis_title=groupby.title(),
            yaxis_title="Number of Interactions",
            legend_title="Interaction Type",
            barmode="stack",
        )

        return fig

    def create_horizontal_bar_chart(
        self, df: pd.DataFrame, category: str = "repository_name", top_n: int = 15
    ) -> go.Figure:
        """Create horizontal bar chart for top repositories, users, or organizations."""
        if df.empty or category not in df.columns:
            fig = go.Figure()
            fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
            return fig

        # Filter out None values and count interactions
        filtered_df = df[df[category].notna()]
        if filtered_df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
            return fig

        counts = filtered_df[category].value_counts().head(top_n)

        fig = go.Figure(
            go.Bar(
                x=counts.values,
                y=counts.index,
                orientation="h",
                marker_color="lightblue",
            )
        )

        fig.update_layout(
            title=f"Top {top_n} {category.replace('_', ' ').title()}s by Interactions",
            xaxis_title="Number of Interactions",
            yaxis_title=category.replace("_", " ").title(),
            height=max(400, top_n * 25),
        )

        return fig

    def create_metrics_cards(self, df: pd.DataFrame) -> dict[str, any]:
        """Create metrics cards with key statistics."""
        if df.empty:
            return {
                "total_interactions": 0,
                "unique_repos": 0,
                "unique_users": 0,
                "date_range": "No data",
                "most_active_day": "No data",
                "growth_rate": 0,
            }

        # Calculate basic metrics
        total_interactions = len(df)
        unique_repos = (
            df["repository_name"].nunique() if "repository_name" in df.columns else 0
        )
        unique_users = df["user"].nunique() if "user" in df.columns else 0

        # Date range
        if "timestamp" in df.columns:
            min_date = df["timestamp"].min().strftime("%Y-%m-%d")
            max_date = df["timestamp"].max().strftime("%Y-%m-%d")
            date_range = f"{min_date} to {max_date}"
        else:
            date_range = "Unknown"

        # Most active day
        if "day_of_week" in df.columns:
            most_active_day = df["day_of_week"].value_counts().index[0]
        else:
            most_active_day = "Unknown"

        # Growth rate (last 7 days vs previous 7 days)
        growth_rate = 0
        if "timestamp" in df.columns and len(df) > 0:
            now = datetime.now()
            last_week = df[df["timestamp"] >= (now - timedelta(days=7))]
            prev_week = df[
                (df["timestamp"] >= (now - timedelta(days=14)))
                & (df["timestamp"] < (now - timedelta(days=7)))
            ]

            if len(prev_week) > 0:
                growth_rate = ((len(last_week) - len(prev_week)) / len(prev_week)) * 100

        return {
            "total_interactions": total_interactions,
            "unique_repos": unique_repos,
            "unique_users": unique_users,
            "date_range": date_range,
            "most_active_day": most_active_day,
            "growth_rate": round(growth_rate, 1),
        }

    def create_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """Create heatmap showing activity patterns by day of week and hour."""
        if df.empty or "timestamp" not in df.columns:
            fig = go.Figure()
            fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
            return fig

        # Create hour and day of week columns if not present
        if "hour" not in df.columns:
            df["hour"] = df["timestamp"].dt.hour
        if "day_of_week" not in df.columns:
            df["day_of_week"] = df["timestamp"].dt.strftime("%A")

        # Create pivot table for heatmap
        heatmap_data = (
            df.groupby(["day_of_week", "hour"]).size().reset_index(name="count")
        )
        pivot_table = heatmap_data.pivot(
            index="day_of_week", columns="hour", values="count"
        ).fillna(0)

        # Reorder days of week
        day_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        pivot_table = pivot_table.reindex(day_order)

        fig = go.Figure(
            data=go.Heatmap(
                z=pivot_table.values,
                x=[f"{h}:00" for h in pivot_table.columns],
                y=pivot_table.index,
                colorscale="Blues",
                hoverongaps=False,
            )
        )

        fig.update_layout(
            title="Activity Heatmap: Interactions by Day and Hour",
            xaxis_title="Hour of Day",
            yaxis_title="Day of Week",
        )

        return fig

    def create_interaction_type_pie(self, df: pd.DataFrame) -> go.Figure:
        """Create pie chart showing distribution of interaction types."""
        if df.empty or "type" not in df.columns:
            fig = go.Figure()
            fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
            return fig

        type_counts = df["type"].value_counts()

        fig = go.Figure(
            data=[go.Pie(labels=type_counts.index, values=type_counts.values, hole=0.3)]
        )

        fig.update_layout(
            title="Distribution of Interaction Types",
            annotations=[
                dict(text="Types", x=0.5, y=0.5, font_size=20, showarrow=False)
            ],
        )

        return fig


def display_metrics_cards(metrics: dict[str, any]):
    """Display metrics as Streamlit cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Interactions",
            value=f"{metrics['total_interactions']:,}",
            delta=f"{metrics['growth_rate']}%" if metrics["growth_rate"] != 0 else None,
        )

    with col2:
        st.metric(label="Unique Repositories", value=metrics["unique_repos"])

    with col3:
        st.metric(label="Unique Users", value=metrics["unique_users"])

    with col4:
        st.metric(label="Most Active Day", value=metrics["most_active_day"])

    st.caption(f"Data range: {metrics['date_range']}")


def export_to_csv(df: pd.DataFrame, filename: str = None) -> str:
    """Export DataFrame to CSV and return download link."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"github_stats_export_{timestamp}.csv"

    csv_data = df.to_csv(index=False)
    return csv_data
