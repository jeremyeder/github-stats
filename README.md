# GitHub Stats

Track interactions with GitHub organizations and repositories.

## Features

- **Comprehensive tracking** - commits, pull requests, issues, stars, forks, releases, workflow runs, and API calls
- **Email reports** - automated daily/weekly/monthly reports with HTML and text formats
- **Scheduled reporting** - automated email reports with customizable schedules
- Support for multiple organizations and repositories
- SQLite database for storing interaction history
- Rich CLI interface with statistics and reporting
- Rate limit monitoring
- Efficient GitHub API usage with pagination support

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/github-stats.git
cd github-stats

# Install in development mode
pip install -e ".[dev]"
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Add your GitHub personal access token to `.env`:
```
GITHUB_TOKEN=your_github_personal_access_token_here
```

To create a GitHub token:
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`

### Email Configuration (Optional)

For email reports, add to your `.env` file:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
```

## Usage

### Initialize the database

```bash
github-stats init
```

### Track organizations

```bash
# Track an organization
github-stats track-org microsoft

# Track an organization and all its repositories
github-stats track-org microsoft --fetch-repos
```

### Track repositories

```bash
# Track a repository (automatically fetches commits, issues, and pull requests)
github-stats track-repo microsoft/vscode

# Track a repository with organization context
github-stats track-repo myrepo --org myorganization
```

### View statistics

```bash
# Show interaction statistics for the last 7 days
github-stats stats

# Filter by organization
github-stats stats --org microsoft

# Filter by repository
github-stats stats --repo microsoft/vscode

# Show statistics for the last 30 days
github-stats stats --days 30
```

### List tracked entities

```bash
# List all tracked organizations
github-stats list-orgs

# List all tracked repositories
github-stats list-repos

# List repositories for a specific organization
github-stats list-repos --org microsoft
```

### Check rate limits

```bash
github-stats rate-limit
```

### Email reports

```bash
# Send a manual email report
github-stats send-report user@example.com --days 7

# Send report for specific organization
github-stats send-report user@example.com --org microsoft --days 30

# Schedule automated reports
github-stats schedule-reports user@example.com --daily --time 09:00
github-stats schedule-reports user@example.com --weekly --time 09:00 --org myorg
```

## Database Schema

The application uses SQLite with the following main tables:

- **organizations**: GitHub organizations being tracked
- **repositories**: GitHub repositories being tracked
- **interactions**: Records of all GitHub interactions

## Development

### Run tests

```bash
pytest
```

### Code formatting and linting

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy github_stats
```

## License

MIT License