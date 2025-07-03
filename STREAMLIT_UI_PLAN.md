# Streamlit Web UI Implementation Plan

## Architecture Analysis
Based on codebase analysis, the GitHub Stats app has:
- **SQLAlchemy models**: Organizations, Repositories, Interactions with relationships
- **11 InteractionTypes**: API_CALL, COMMIT, PULL_REQUEST, ISSUE, COMMENT, REVIEW, FORK, STAR, WATCH, RELEASE, WORKFLOW_RUN  
- **Existing query patterns**: Time-based filtering, org/repo filtering, aggregation by type/user/repo
- **Pydantic config**: Settings with environment variables, database URL flexibility
- **Rich templating**: HTML email templates with styling already exists

## Phase 1: Foundation (Start Simple)
1. **Add dependencies** to pyproject.toml:
   ```
   "streamlit>=1.28.0",
   "plotly>=5.17.0", 
   "pandas>=2.0.0"
   ```

2. **Create streamlit_app.py** entry point:
   - Basic multi-page app structure using st.navigation
   - Reuse existing database connection patterns from utils/database.py
   - Import existing models and query patterns

## Phase 2: Query Builder Interface (Mirror CLI Functionality)
3. **Create github_stats/ui/query_builder.py**:
   ```python
   # Sidebar filters matching CLI parameters:
   - Organization multiselect (from tracked orgs in DB)
   - Repository multiselect (filtered by selected orgs) 
   - InteractionType multiselect (from enum)
   - Date range picker (start_date, end_date) instead just "days"
   - User filter (from distinct users in interactions)
   ```

4. **Create github_stats/ui/data_service.py**:
   - Reuse existing query patterns from email_reporter.py
   - Add time-series aggregation (daily/weekly/monthly grouping)
   - Add methods for org/repo/user lists for dropdowns

## Phase 3: Visualization Engine (Simple Charts First)
5. **Create github_stats/ui/charts.py**:
   ```python
   # Chart types focusing on trends:
   - Time series line chart (interactions over time by type)
   - Stacked bar chart (interaction types by day/week)
   - Horizontal bar chart (top repos/users/orgs)
   - Simple metrics cards (total counts, growth rates)
   ```

6. **Visualization Page**:
   - Query builder in sidebar
   - Main area with generated charts
   - Raw data table toggle (expandable)
   - Simple export to CSV button

## Phase 4: Dashboard System (Keep It Simple)
7. **Query Persistence**:
   - Save queries as JSON to local file (not database initially)
   - Simple naming system for saved queries
   - Load/delete saved queries

8. **Dashboard Page**:
   - Grid layout with saved query results
   - Refresh all/individual panels
   - Simple drag-and-drop reordering later

## Phase 5: Integration & Polish
9. **Create streamlit_app.py launcher**:
   ```python
   # Simple entry point that:
   - Checks database exists (auto-init if not)
   - Sets up logging
   - Launches main UI
   ```

10. **Update pyproject.toml**:
   ```
   [project.scripts]
   github-stats-ui = "github_stats.ui.streamlit_app:main"
   ```

## File Structure (Minimal)
```
github_stats/
  ui/
    __init__.py
    streamlit_app.py    # Main entry point
    query_builder.py    # Query form components  
    data_service.py     # Database query logic
    charts.py           # Plotting functions
    dashboard.py        # Dashboard management
  streamlit_app.py      # Top-level launcher
```

## Success Criteria (MVP)
- [ ] Users can select org/repo/date ranges like CLI
- [ ] Generate time-series and bar charts showing trends
- [ ] Save and load simple query configurations  
- [ ] Export data to CSV
- [ ] Runs with `streamlit run streamlit_app.py`

## Key Design Principles Applied
- **Reuse existing code**: Database models, query patterns, settings
- **Simple file persistence**: Avoid over-engineering dashboard storage
- **Progressive enhancement**: Start with basic charts, add complexity later
- **Mirror CLI functionality**: Users familiar with CLI can use UI immediately
- **Progress over perfection**: Focus on working functionality first

---

## How to Resume This Implementation

### Resume Command
```bash
# Tell Claude to resume from this plan:
claude read STREAMLIT_UI_PLAN.md

# Or be more specific:
claude "Continue implementing the Streamlit UI from STREAMLIT_UI_PLAN.md, starting with Phase 1"
```

### Current Status
- ✅ Plan saved to STREAMLIT_UI_PLAN.md
- ⏳ Ready to start Phase 1: Add dependencies and create basic structure

### Next Steps
1. Add Streamlit dependencies to pyproject.toml
2. Create the ui/ directory structure
3. Implement data_service.py with database queries
4. Build query_builder.py with form components
5. Continue with remaining phases

### Context Commands
```bash
# Check current todo status:
claude "Read my current todo list and continue with Streamlit UI implementation"

# Quick status check:
claude "What's the status of the Streamlit UI implementation?"

# Jump to specific phase:
claude "Skip to Phase 3 and implement the visualization charts"
```