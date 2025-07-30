import asyncio
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
import json
import httpx
from datetime import datetime

from app.schemas.alerts import Alert, NotificationChannel, NotificationLog
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications through various channels"""
    
    def __init__(self):
        self.notification_logs = []
    
    async def send_alert_notification(self, alert: Alert) -> List[NotificationLog]:
        """Send alert notification through configured channels"""
        try:
            logs = []
            
            # Determine notification channels based on severity
            channels = self._get_notification_channels_for_severity(alert.severity)
            
            for channel in channels:
                try:
                    log = await self._send_notification(alert, channel)
                    logs.append(log)
                    
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel}: {e}")
                    # Create error log
                    error_log = NotificationLog(
                        alert_id=alert.id,
                        channel=channel,
                        recipient="unknown",
                        subject=f"Alert: {alert.title}",
                        message="Failed to send notification",
                        status="failed",
                        error_message=str(e)
                    )
                    logs.append(error_log)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")
            raise
    
    async def _send_notification(
        self,
        alert: Alert,
        channel: NotificationChannel
    ) -> NotificationLog:
        """Send notification via specific channel"""
        
        if channel == NotificationChannel.EMAIL:
            return await self._send_email_notification(alert)
        elif channel == NotificationChannel.SLACK:
            return await self._send_slack_notification(alert)
        elif channel == NotificationChannel.WEBHOOK:
            return await self._send_webhook_notification(alert)
        else:
            raise ValueError(f"Unsupported notification channel: {channel}")
    
    async def _send_email_notification(self, alert: Alert) -> NotificationLog:
        """Send email notification"""
        try:
            if not settings.ALERT_EMAIL_ENABLED:
                raise ValueError("Email notifications are disabled")
            
            # Prepare email content
            subject = f"[{alert.severity.upper()}] Data Quality Alert: {alert.title}"
            body = self._format_email_body(alert)
            
            # Get recipients (in production, this would come from user settings)
            recipients = self._get_email_recipients_for_alert(alert)
            
            # Send email using SMTP
            if settings.SMTP_HOST and settings.SMTP_USER:
                await self._send_smtp_email(recipients, subject, body)
                status = "sent"
                error_message = None
            else:
                # Simulate email sending in development
                logger.info(f"Simulated email sent to {recipients}: {subject}")
                status = "simulated"
                error_message = None
            
            return NotificationLog(
                alert_id=alert.id,
                channel=NotificationChannel.EMAIL,
                recipient=", ".join(recipients),
                subject=subject,
                message=body,
                status=status,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            raise
    
    async def _send_slack_notification(self, alert: Alert) -> NotificationLog:
        """Send Slack notification"""
        try:
            if not settings.ALERT_SLACK_ENABLED:
                raise ValueError("Slack notifications are disabled")
            
            # Prepare Slack message
            message = self._format_slack_message(alert)
            
            if settings.SLACK_WEBHOOK_URL:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        settings.SLACK_WEBHOOK_URL,
                        json=message,
                        timeout=30
                    )
                    response.raise_for_status()
                
                status = "sent"
                error_message = None
            else:
                # Simulate Slack notification
                logger.info(f"Simulated Slack notification: {message}")
                status = "simulated"
                error_message = None
            
            return NotificationLog(
                alert_id=alert.id,
                channel=NotificationChannel.SLACK,
                recipient="slack-channel",
                subject=f"Data Quality Alert: {alert.title}",
                message=json.dumps(message),
                status=status,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            raise
    
    async def _send_webhook_notification(self, alert: Alert) -> NotificationLog:
        """Send webhook notification"""
        try:
            # Prepare webhook payload
            payload = {
                "alert_id": str(alert.id),
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity,
                "dataset_id": alert.dataset_id,
                "status": alert.status,
                "created_at": alert.created_at.isoformat(),
                "metadata": alert.metadata
            }
            
            # In production, webhook URL would be configurable per alert rule
            webhook_url = "https://example.com/webhook"  # Mock URL
            
            # Simulate webhook sending
            logger.info(f"Simulated webhook sent to {webhook_url}: {payload}")
            
            return NotificationLog(
                alert_id=alert.id,
                channel=NotificationChannel.WEBHOOK,
                recipient=webhook_url,
                subject=f"Alert Webhook: {alert.title}",
                message=json.dumps(payload),
                status="simulated"
            )
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            raise
    
    async def _send_smtp_email(
        self,
        recipients: List[str],
        subject: str,
        body: str
    ):
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipients}")
            
        except Exception as e:
            logger.error(f"Failed to send SMTP email: {e}")
            raise
    
    def _get_notification_channels_for_severity(
        self,
        severity: str
    ) -> List[NotificationChannel]:
        """Get notification channels based on alert severity"""
        
        # Map severity to notification channels
        severity_channels = {
            "low": [NotificationChannel.EMAIL],
            "medium": [NotificationChannel.EMAIL, NotificationChannel.SLACK],
            "high": [NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.WEBHOOK],
            "critical": [NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.WEBHOOK]
        }
        
        return severity_channels.get(severity, [NotificationChannel.EMAIL])
    
    def _get_email_recipients_for_alert(self, alert: Alert) -> List[str]:
        """Get email recipients for an alert"""
        # In production, this would query user database for dataset owners/subscribers
        return ["data-team@company.com", "data-quality@company.com"]
    
    def _format_email_body(self, alert: Alert) -> str:
        """Format email body for alert"""
        return f"""
        <html>
        <head></head>
        <body>
            <h2 style="color: {'red' if alert.severity in ['high', 'critical'] else 'orange'};">
                Data Quality Alert: {alert.title}
            </h2>
            
            <p><strong>Dataset:</strong> {alert.dataset_id}</p>
            <p><strong>Severity:</strong> {alert.severity.upper()}</p>
            <p><strong>Status:</strong> {alert.status}</p>
            <p><strong>Created:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            
            <h3>Description</h3>
            <p>{alert.description}</p>
            
            <h3>Additional Information</h3>
            <ul>
                {"".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in alert.metadata.items()])}
            </ul>
            
            <p>
                <a href="http://localhost:3000/alerts/{alert.id}" 
                   style="background-color: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    View Alert Details
                </a>
            </p>
            
            <hr>
            <p style="font-size: 12px; color: #666;">
                This is an automated message from the Data Quality Platform.
            </p>
        </body>
        </html>
        """
    
    def _format_slack_message(self, alert: Alert) -> Dict[str, Any]:
        """Format Slack message for alert"""
        
        # Choose color based on severity
        color_map = {
            "low": "#36a64f",      # Green
            "medium": "#ffb347",   # Orange
            "high": "#ff6b47",     # Red-orange
            "critical": "#ff0000"  # Red
        }
        
        color = color_map.get(alert.severity, "#ffb347")
        
        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"Data Quality Alert: {alert.title}",
                    "title_link": f"http://localhost:3000/alerts/{alert.id}",
                    "text": alert.description,
                    "fields": [
                        {
                            "title": "Dataset",
                            "value": alert.dataset_id,
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": alert.severity.upper(),
                            "short": True
                        },
                        {
                            "title": "Status",
                            "value": alert.status,
                            "short": True
                        },
                        {
                            "title": "Created",
                            "value": alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
                            "short": True
                        }
                    ],
                    "footer": "Data Quality Platform",
                    "footer_icon": "https://platform.com/icon.png",
                    "ts": int(alert.created_at.timestamp())
                }
            ]
        }
    
    async def send_test_notification(
        self,
        channel: NotificationChannel,
        recipient: str
    ) -> bool:
        """Send test notification to verify channel configuration"""
        try:
            test_alert = Alert(
                title="Test Notification",
                description="This is a test notification from the Data Quality Platform.",
                dataset_id="test-dataset",
                severity="low"
            )
            
            log = await self._send_notification(test_alert, channel)
            return log.status in ["sent", "simulated"]
            
        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            return False
    
    def get_notification_history(
        self,
        alert_id: Optional[str] = None,
        limit: int = 100
    ) -> List[NotificationLog]:
        """Get notification history"""
        logs = self.notification_logs
        
        if alert_id:
            logs = [log for log in logs if str(log.alert_id) == alert_id]
        
        return logs[:limit]
