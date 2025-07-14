# DNC Automator - Claude Development Assistant Guide

## Project Overview
This project transforms an existing manual DNC (Do Not Call) checking system into a fully automated HubSpot integration. The system will:
- Check company-level matches using fuzzy matching (90% threshold for auto-action, 85% for review)
- Update both company and contact lifecycle statuses in HubSpot
- Run automatically via GitHub Actions
- Send email notifications with results
- Handle multiple client configurations

## Core Repository Integration
The existing DNC matching logic is located at: https://github.com/Jonathan-hanekom-punchb2b/dnc_checker
This logic needs to be extracted and adapted for HubSpot integration.

## Development Commands
```bash
# Environment setup
uv sync --dev                              # Install dependencies
source .venv/bin/activate                  # Activate virtual environment (Linux/Mac)
.venv\Scripts\activate                     # Activate virtual environment (Windows)

# Testing
uv run pytest tests/ -v                    # Run all tests
uv run pytest tests/unit/ -v               # Run unit tests only
uv run pytest tests/integration/ -v        # Run integration tests only
uv run pytest tests/ -v --cov=src          # Run tests with coverage

# Linting and formatting
uv run black src/                          # Format code
uv run isort src/                          # Sort imports
uv run flake8 src/                         # Check style
uv run mypy src/                           # Type checking

# Manual testing
uv run python tests/manual_hubspot_test.py # Test HubSpot connection
uv run python scripts/test_email.py        # Test email notifications
uv run python src/main.py                  # Run full automation

# Monitoring
uv run python scripts/monitor_runs.py      # Analyze recent runs
uv run python scripts/performance_monitor.py # Performance analysis
```

## Project Structure
```
dnc_automator/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── dnc_logic.py          # Enhanced DNC matching logic
│   │   └── config.py             # Configuration management
│   ├── hubspot/
│   │   ├── __init__.py
│   │   ├── client.py             # HubSpot API wrapper
│   │   ├── models.py             # Data models
│   │   └── auth.py               # Authentication handling
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── email_sender.py       # Email notifications
│   │   └── templates.py          # Email templates
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_handler.py       # File upload/processing
│   │   ├── logger.py             # Logging configuration
│   │   └── validators.py         # Data validation
│   └── main.py                   # Main orchestration script
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── data/
│   ├── uploads/                  # Incoming DNC lists
│   ├── processed/                # Processed lists
│   └── archived/                 # Historical data
├── logs/                         # Application logs
├── config/
│   ├── clients.yaml              # Client configurations
│   └── hubspot_mappings.yaml     # Field mappings
├── .github/workflows/
│   └── dnc_automation.yml        # GitHub Actions workflow
├── .env.example                  # Environment variables template
├── pyproject.toml               # Project dependencies
└── CLAUDE.md                    # This file
```

## Key Components

### 1. DNC Logic (`src/core/dnc_logic.py`)
- **Purpose**: Enhanced fuzzy matching logic adapted from existing repository
- **Key Features**:
  - Exact name matching (100% confidence)
  - Domain-based matching (100% confidence)
  - Fuzzy name matching with configurable thresholds
  - Supports 90% threshold for auto-action, 85% for review
- **Input**: HubSpot companies + DNC CSV data
- **Output**: List of matches with confidence scores and recommended actions

### 2. HubSpot Client (`src/hubspot/client.py`)
- **Purpose**: Wrapper for HubSpot API operations
- **Key Features**:
  - Fetch all companies with pagination
  - Get contacts associated with companies
  - Batch update company and contact statuses
  - Rate limiting and error handling
- **Authentication**: Private App API key
- **Required Scopes**:
  - `crm.objects.contacts.read`
  - `crm.objects.contacts.write`
  - `crm.objects.companies.read` 
  - `crm.objects.companies.write`

### 3. Email Notifications (`src/notifications/email_sender.py`)
- **Purpose**: Send automated email summaries and error reports
- **Templates**: HTML templates for success and error notifications
- **Features**:
  - Run summaries with metrics
  - Error notifications with stack traces
  - File attachments for detailed results
  - Support for multiple recipients

### 4. Main Orchestration (`src/main.py`)
- **Purpose**: Coordinate all components in complete workflow
- **Workflow**:
  1. Load and validate DNC list
  2. Fetch HubSpot companies
  3. Check for matches using enhanced logic
  4. Update company and contact statuses
  5. Generate results and send notifications
- **Error Handling**: Comprehensive error capture and notification

## Environment Configuration
```bash
# HubSpot Configuration
HUBSPOT_API_KEY=your_hubspot_api_key_here
HUBSPOT_INSTANCE_NAME=your_instance_name

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@company.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENTS=you@company.com,datamanager@company.com,depthead@company.com

# Application Configuration
LOG_LEVEL=INFO
FUZZY_THRESHOLD_MATCH=90
FUZZY_THRESHOLD_REVIEW=85
COMPANY_BATCH_SIZE=100
CONTACT_BATCH_SIZE=500

# Client Configuration
CLIENT_NAME=test_client
COMPANY_STATUS_PROPERTY=test_client_account_status
CONTACT_STATUS_PROPERTY=test_client_funnel_status

# File paths
DNC_UPLOAD_PATH=data/uploads
DNC_PROCESSED_PATH=data/processed
DNC_ARCHIVED_PATH=data/archived
```

## Development Workflow

### Phase 1: Setup and Core Logic (Week 1)
1. **Repository Setup**: Clone existing repo and create automation branch
2. **HubSpot API Setup**: Create private app and test connection
3. **Core Logic Integration**: Adapt existing DNC logic for HubSpot data

### Phase 2: HubSpot Integration (Week 2)
1. **Build HubSpot Client**: Create API wrapper with error handling
2. **Integration Testing**: Test with sample data from HubSpot
3. **Error Handling**: Implement comprehensive error handling

### Phase 3: Automation (Week 3)
1. **GitHub Actions**: Create workflow for scheduled runs
2. **Secrets Management**: Configure secure credential storage
3. **Testing**: End-to-end automation testing

### Phase 4: Production Features (Week 4)
1. **Email Notifications**: Implement summary and error emails
2. **File Upload**: Handle DNC list uploads
3. **Monitoring**: Add performance monitoring and logging

## Testing Strategy

### Unit Tests
- Test individual functions in isolation
- Mock HubSpot API calls
- Test DNC matching logic with known data
- Validate email template generation

### Integration Tests
- Test with mock HubSpot data
- Test complete workflow with sample clients
- Validate error handling scenarios

### Manual Testing
- Test HubSpot connection with real API
- Verify email notifications work
- Test with small dataset in HubSpot
- Validate status updates are correct

## Key Matching Logic
The system uses a three-tier matching approach:

1. **Exact Match** (100% confidence → auto-exclude):
   - Exact company name match (case-insensitive)
   - Domain match (normalized)

2. **Fuzzy Match** (configurable thresholds):
   - 90%+ confidence → auto-exclude (update status to "Client Working")
   - 85-89% confidence → manual review required
   - <85% confidence → no action

3. **Status Updates**:
   - Company status → "Client Working" 
   - Associated contact status → "On Hold"

## Error Handling
- API rate limiting with automatic retries
- Network timeout handling
- Invalid data validation
- Comprehensive logging for debugging
- Email notifications for all errors
- Graceful degradation when possible

## Monitoring and Maintenance
- Performance monitoring with CPU/memory tracking
- Run history analysis and reporting
- Log rotation and archival
- Automated cleanup of old processed files
- Dashboard for run statistics

## Security Considerations
- API keys stored as GitHub secrets
- No sensitive data in code or logs
- Secure email authentication (app passwords)
- Input validation for all data sources
- Rate limiting to prevent API abuse

## Troubleshooting

### Common Issues
1. **HubSpot API Connection**: Verify API key and scopes
2. **Email Notifications**: Check SMTP settings and app passwords
3. **GitHub Actions**: Verify secrets are configured correctly
4. **Data Processing**: Validate CSV format and encoding

### Emergency Procedures
1. **Disable automation**: Turn off GitHub Actions workflow
2. **Rollback**: Revert to previous working version
3. **Manual process**: Return to existing manual DNC checker
4. **Data recovery**: Use HubSpot activity logs to identify changes

## Success Metrics
- **Automation Success**: Scheduled runs complete without errors
- **Accuracy**: Match confidence scores align with manual review
- **Performance**: Process 1000+ companies in under 10 minutes
- **Reliability**: 99%+ uptime for scheduled runs
- **User Satisfaction**: Email summaries provide clear, actionable information

## Future Enhancements
- Web interface for DNC list uploads
- Advanced matching algorithms
- Multi-client support with separate configurations
- Dashboard for run analytics
- Integration with other CRM systems

## Support and Documentation
- Check troubleshooting guide for common issues
- Review logs in GitHub Actions for run details
- Email notifications provide run summaries
- Contact development team for complex issues

This guide provides comprehensive information for developing, testing, and maintaining the DNC automation system. The modular architecture allows for incremental development and easy maintenance.