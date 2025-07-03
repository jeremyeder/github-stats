# Query Builder Development Plan - Current Status

## Phase 1: UI Mockup ✅ COMPLETED
- [x] Create query_builder.py component with main UI structure
- [x] Implement query builder form with filters (org, repo, user, interaction type, action, date range)
- [x] Add query preview section with SQL display and validation
- [x] Create results section with mock data table and pagination
- [x] Add visualization options with sample charts (bar, line, pie)
- [x] Implement saved queries section with save/load functionality
- [x] Add export options (CSV, JSON, Excel) with mock downloads
- [x] Update main app.py to include Query Builder in navigation
- [x] Test complete UI mockup functionality
- [x] Fix plotly import issues for Python 3.13 compatibility
- [x] Add geckodriver installation script with jq support
- [x] Update documentation

## Phase 2: Replace Mock Data with Real Database Queries 🔄 IN PROGRESS

### Current Issue Identified:
The Query Builder currently uses hardcoded mock data (google, microsoft, etc.) which is misleading. Need to replace with actual database queries.

### Next Tasks:
- [ ] **PRIORITY**: Remove hardcoded mock organizations/repositories from query_builder.py
- [ ] Replace MOCK_ORGANIZATIONS with database query for actual organizations
- [ ] Replace MOCK_REPOSITORIES with database query for actual repositories  
- [ ] Replace MOCK_USERS with database query for actual users from interactions
- [ ] Replace MOCK_ACTIONS with database query for actual actions from interactions
- [ ] Update dropdowns to default to empty when no data exists
- [ ] Implement real database query execution (replace generate_mock_results())
- [ ] Connect filters to actual SQLAlchemy queries
- [ ] Replace mock chart data with real data from database
- [ ] Add proper error handling for empty database
- [ ] Test with actual GitHub data

### Implementation Notes:
- File location: `/Users/jeder/repos/github-stats/streamlit_app/components/query_builder.py`
- Database models available: Organization, Repository, Interaction from github_stats.models.interactions
- Database access pattern: Use `get_db()` context manager like other components
- Current mock data to replace:
  - MOCK_ORGANIZATIONS (lines 17-19)
  - MOCK_REPOSITORIES (lines 21-25) 
  - MOCK_USERS (lines 27-31)
  - MOCK_ACTIONS (lines 33-37)
  - generate_mock_results() function (lines 39-57)
  - generate_mock_chart_data() function (lines 59-82)

### Database Query Patterns to Use:
```python
# Get organizations
organizations = session.query(Organization.name).all()

# Get repositories  
repositories = session.query(Repository.full_name).all()

# Get users
users = session.query(Interaction.user).filter(Interaction.user.isnot(None)).distinct().all()

# Get actions
actions = session.query(Interaction.action).filter(Interaction.action.isnot(None)).distinct().all()
```

## Phase 3: Advanced Features (Future)
- [ ] Save/load query functionality with database persistence
- [ ] Query templates and sharing
- [ ] Advanced visualization options
- [ ] Real export functionality
- [ ] Query performance optimization
- [ ] User permissions and access control

## Current Status
- **Phase 1**: ✅ Complete - UI mockup fully functional
- **Phase 2**: 🔄 Ready to start - Replace mock data with real database queries
- **Next Action**: Remove hardcoded mock data and implement database queries

## Context
- User noticed the misleading mock data (google, microsoft, etc.) 
- Query Builder should show empty dropdowns when no data exists
- Need to maintain UI functionality while switching to real data
- All database models and access patterns already established in other components