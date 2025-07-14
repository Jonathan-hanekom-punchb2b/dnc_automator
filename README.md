# DNC Automation System

Automated Do Not Call (DNC) checking and HubSpot integration system that transforms manual DNC processes into fully automated workflows.

## Features

- **Automated DNC Checking**: Fuzzy matching (90% threshold for auto-action, 85% for review)
- **HubSpot Integration**: Updates company and contact lifecycle statuses
- **Scheduled Automation**: Runs automatically via GitHub Actions
- **Email Notifications**: Sends summaries and error reports
- **Multi-Client Support**: Handles different client configurations

## Quick Start

1. **Clone repository**:
   ```bash
   git clone https://github.com/Jonathan-hanekom-punchb2b/dnc_automator.git
   cd dnc_automator
   ```

2. **Install dependencies**:
   ```bash
   uv sync --dev
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

4. **Test setup**:
   ```bash
   uv run python -c "from src.hubspot.client import HubSpotClient; print('Setup successful!')"
   ```

5. **Run automation**:
   ```bash
   uv run python src/main.py
   ```

## Configuration

### Required Environment Variables

- `HUBSPOT_API_KEY`: HubSpot Private App API key
- `EMAIL_USERNAME`: SMTP email username
- `EMAIL_PASSWORD`: SMTP email password (use app password for Gmail)
- `CLIENT_NAME`: Client identifier for file naming
- `COMPANY_STATUS_PROPERTY`: HubSpot company property to update
- `CONTACT_STATUS_PROPERTY`: HubSpot contact property to update

### HubSpot Setup

1. Create a HubSpot Private App:
   - Go to HubSpot → Settings → Integrations → Private Apps
   - Create new app with required scopes:
     - `crm.objects.contacts.read`
     - `crm.objects.contacts.write`
     - `crm.objects.companies.read`
     - `crm.objects.companies.write`

2. Save the API key to your `.env` file

## Usage

### Manual Runs

Run the automation manually:
```bash
uv run python src/main.py
```

### Scheduled Automation

The system runs automatically via GitHub Actions:
- **Schedule**: Mondays and Thursdays at 9 AM UTC
- **Manual trigger**: Available through GitHub Actions interface

### File Upload

Place DNC files in the `data/uploads/` directory with naming pattern:
```
{client_name}_{dd-mm-yy}.csv
```

Required CSV columns:
- `company_name`: Company name to match
- `domain`: Company domain (optional)

## Development

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --cov=src

# Run specific test file
uv run pytest tests/unit/test_dnc_logic.py -v
```

### Code Quality

```bash
# Format code
uv run black src/

# Sort imports
uv run isort src/

# Check style
uv run flake8 src/

# Type checking
uv run mypy src/
```

## Monitoring

- **Email notifications**: Automatic summaries and error reports
- **GitHub Actions logs**: Detailed run information
- **Results storage**: CSV files in `data/results/` directory

## Architecture

```
src/
├── core/           # DNC matching logic
├── hubspot/        # HubSpot API integration
├── notifications/  # Email system
├── utils/          # Utilities and helpers
└── main.py         # Main orchestration
```

## Troubleshooting

### Common Issues

1. **HubSpot API Error**: Check API key and scopes
2. **Email Failure**: Verify SMTP settings and app password
3. **File Not Found**: Check file naming and location
4. **Permission Error**: Ensure proper HubSpot permissions

### Error Recovery

If automation fails:
1. Check GitHub Actions logs
2. Review email error notifications
3. Verify environment variables
4. Test individual components

## Support

For issues and questions:
- Review the troubleshooting guide in `CLAUDE.md`
- Check GitHub Actions logs for run details
- Contact the development team for complex issues

## License

This project is proprietary software for internal use only.