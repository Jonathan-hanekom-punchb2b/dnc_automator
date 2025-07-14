"""
Email notification system for DNC automation
Sends summaries and error reports with HTML templates
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any
from jinja2 import Template
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Handles email notifications for DNC automation"""
    
    def __init__(self, 
                 smtp_host: str,
                 smtp_port: int,
                 username: str,
                 password: str,
                 recipients: List[str]):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipients = recipients
    
    def send_success_summary(self, 
                           run_summary: Dict[str, Any],
                           attachment_path: str = None) -> bool:
        """Send successful run summary email"""
        
        subject = f"DNC Check Complete - {run_summary['client_name']} - {datetime.now().strftime('%Y-%m-%d')}"
        
        html_content = self._generate_success_email(run_summary)
        
        return self._send_email(
            subject=subject,
            html_content=html_content,
            attachment_path=attachment_path
        )
    
    def send_error_notification(self, 
                              error_details: Dict[str, Any]) -> bool:
        """Send error notification email"""
        
        subject = f"DNC Automation Error - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        html_content = self._generate_error_email(error_details)
        
        return self._send_email(
            subject=subject,
            html_content=html_content
        )
    
    def _generate_success_email(self, summary: Dict[str, Any]) -> str:
        """Generate HTML content for success email"""
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #28a745; color: white; padding: 10px; border-radius: 5px; }
                .summary-box { background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .metric { display: inline-block; margin: 10px 20px 10px 0; }
                .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
                .metric-label { font-size: 14px; color: #6c757d; }
                .matches-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                .matches-table th, .matches-table td { border: 1px solid #dee2e6; padding: 8px; text-align: left; }
                .matches-table th { background-color: #e9ecef; }
                .footer { margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>✅ DNC Check Completed Successfully</h2>
            </div>
            
            <div class="summary-box">
                <h3>Run Summary</h3>
                <div class="metric">
                    <div class="metric-value">{{ summary.companies_checked }}</div>
                    <div class="metric-label">Companies Checked</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ summary.matches_found }}</div>
                    <div class="metric-label">DNC Matches Found</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ summary.companies_updated }}</div>
                    <div class="metric-label">Companies Updated</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ summary.contacts_updated }}</div>
                    <div class="metric-label">Contacts Updated</div>
                </div>
            </div>
            
            <div class="summary-box">
                <h3>Details</h3>
                <p><strong>Client:</strong> {{ summary.client_name }}</p>
                <p><strong>DNC List:</strong> {{ summary.dnc_list_name }}</p>
                <p><strong>Run Time:</strong> {{ summary.start_time }} - {{ summary.end_time }}</p>
                <p><strong>Duration:</strong> {{ summary.duration }}</p>
            </div>
            
            {% if summary.matches %}
            <div class="summary-box">
                <h3>DNC Matches Found</h3>
                <table class="matches-table">
                    <thead>
                        <tr>
                            <th>Company Name</th>
                            <th>DNC List Match</th>
                            <th>Match Type</th>
                            <th>Confidence</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for match in summary.matches %}
                        <tr>
                            <td>{{ match.company_name }}</td>
                            <td>{{ match.dnc_company_name }}</td>
                            <td>{{ match.match_type|title }}</td>
                            <td>{{ "%.1f"|format(match.confidence) }}%</td>
                            <td>{{ match.action|title }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
            
            <div class="footer">
                <p>This email was generated automatically by the DNC Automation System.</p>
                <p>Run ID: {{ summary.run_id }}</p>
            </div>
        </body>
        </html>
        """)
        
        return template.render(summary=summary)
    
    def _generate_error_email(self, error_details: Dict[str, Any]) -> str:
        """Generate HTML content for error email"""
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #dc3545; color: white; padding: 10px; border-radius: 5px; }
                .error-box { background-color: #f8d7da; padding: 15px; margin: 10px 0; border-radius: 5px; border: 1px solid #f5c6cb; }
                .code-block { background-color: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; white-space: pre-wrap; }
                .footer { margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>❌ DNC Automation Error</h2>
            </div>
            
            <div class="error-box">
                <h3>Error Details</h3>
                <p><strong>Error Type:</strong> {{ error_details.error_type }}</p>
                <p><strong>Error Message:</strong> {{ error_details.error_message }}</p>
                <p><strong>Timestamp:</strong> {{ error_details.timestamp }}</p>
                {% if error_details.client_name %}
                <p><strong>Client:</strong> {{ error_details.client_name }}</p>
                {% endif %}
            </div>
            
            {% if error_details.stack_trace %}
            <div class="error-box">
                <h3>Stack Trace</h3>
                <div class="code-block">{{ error_details.stack_trace }}</div>
            </div>
            {% endif %}
            
            {% if error_details.context %}
            <div class="error-box">
                <h3>Additional Context</h3>
                {% for key, value in error_details.context.items() %}
                <p><strong>{{ key }}:</strong> {{ value }}</p>
                {% endfor %}
            </div>
            {% endif %}
            
            <div class="footer">
                <p>Please check the system logs for more details and take appropriate action.</p>
                <p>Run ID: {{ error_details.run_id }}</p>
            </div>
        </body>
        </html>
        """)
        
        return template.render(error_details=error_details)
    
    def _send_email(self, 
                   subject: str,
                   html_content: str,
                   attachment_path: str = None) -> bool:
        """Send email with optional attachment"""
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = ', '.join(self.recipients)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.username, self.recipients, msg.as_string())
            
            logger.info(f"Email sent successfully to {', '.join(self.recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False