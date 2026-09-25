import os
import smtplib
import traceback
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from todoist_automation.api.todoist_client import TodoistException

load_dotenv()


def send_email(subject, body, to):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    usuario = os.getenv('ECLIPSE_EMAIL')
    app_password = os.getenv('ECLIPSE_APP_PASSWORD')

    mensaje = MIMEMultipart()
    mensaje["From"] = usuario
    mensaje["To"] = to
    mensaje["Subject"] = subject
    cuerpo = body
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        servidor = smtplib.SMTP(smtp_server, smtp_port)
        servidor.starttls()
        servidor.login(usuario, app_password)
        servidor.sendmail(usuario, to, mensaje.as_string())
        servidor.quit()
        print("Email sent succesfully")
    except Exception as e:
        print(f"Error sending email: {e}")
        raise e


def build_exception_msg(e: Exception) -> str:
    """
    Build a detailed exception message with the complete traceback.
    
    Args:
        e: The exception to process.
    
    Returns:
        str: Detailed message formatted for email.
    """
    msg_parts = []
    msg_parts.append("=" * 80)
    msg_parts.append("DETAILED ERROR")
    msg_parts.append("=" * 80)
    
    # Basic information
    msg_parts.append(f"\nError type: {type(e).__name__}")
    msg_parts.append(f"Time: {datetime.now().isoformat()}")
    msg_parts.append(f"Message: {str(e)}")
    
    # Additional information for TodoistException
    if isinstance(e, TodoistException):
        msg_parts.append(f"\n" + "=" * 80)
        msg_parts.append("SERVICE INFORMATION")
        msg_parts.append("=" * 80)
        for key, value in e.context.items():
            if key == 'service':
                msg_parts.append(f"\n🔴 FAILED SERVICE: {value.upper()}")
            else:
                msg_parts.append(f"  - {key}: {value}")
    
    # Complete traceback
    msg_parts.append("\n" + "=" * 80)
    msg_parts.append("COMPLETE TRACEBACK")
    msg_parts.append("=" * 80)
    
    tb_str = traceback.format_exc()
    if tb_str == "NoneType: None\n":
        # If there is no traceback, build one from the exception
        tb_str = f"  Exception: {e}\n"
    msg_parts.append(tb_str)
    
    # Root-cause information
    if e.__cause__:
        msg_parts.append("\n" + "=" * 80)
        msg_parts.append("ROOT CAUSE")
        msg_parts.append("=" * 80)
        msg_parts.append(f"Type: {type(e.__cause__).__name__}")
        msg_parts.append(f"Message: {str(e.__cause__)}")
    
    return "\n".join(msg_parts)


def format_error_for_email(operation: str, e: Exception, additional_info: dict = None) -> str:
    """
    Format a complete error for email with operation context.
    
    Args:
        operation: Name of the failed operation (e.g. "Daily Task Execution").
        e: The captured exception.
        additional_info: Dictionary with additional information (e.g. task_id, project_name).
    
    Returns:
        str: Formatted message ready to send by email.
    """
    msg_parts = []
    
    # Header with service identification
    service = "UNKNOWN"
    if isinstance(e, TodoistException) and 'service' in e.context:
        service = e.context['service']
    
    msg_parts.append("\n" + "🚨 " * 20)
    msg_parts.append(f"AFFECTED SERVICE: {service}")
    msg_parts.append("🚨 " * 20)
    
    msg_parts.append("\n" + "=" * 80)
    msg_parts.append(f"FAILED OPERATION: {operation}")
    msg_parts.append("=" * 80)
    msg_parts.append(f"\nDate and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Additional information, if available
    if additional_info:
        msg_parts.append("\nOperation details:")
        for key, value in additional_info.items():
            msg_parts.append(f"  - {key}: {value}")
    
    # Error details
    msg_parts.append("\n" + build_exception_msg(e))
    
    # Recommendations by service
    msg_parts.append("\n" + "=" * 80)
    msg_parts.append("RECOMMENDATIONS")
    msg_parts.append("=" * 80)
    if service == "Todoist API":
        msg_parts.append("• The error comes from the Todoist API")
        msg_parts.append("• Check status: https://todoist.com/")
        msg_parts.append("• Review API rate limits")
        msg_parts.append("• The code will retry automatically on future executions")
    else:
        msg_parts.append("• Review execution logs")
        msg_parts.append("• Check the internet connection")
    
    return "\n".join(msg_parts)
