"""
Email templates for opportunity notifications.
Uses Groq for generating summaries when available.
"""

from typing import List, Optional
from models import Opportunity
from external.groq.client import get_groq_client
from core.logging import get_logger

logger = get_logger(__name__)


def format_opportunity_date(date_str: Optional[str]) -> str:
    """Format opportunity date string for display."""
    if not date_str:
        return "Not specified"
    return date_str


def get_new_opportunity_email_subject(opportunity: Opportunity) -> str:
    """Get email subject for new opportunity notification."""
    name = opportunity.opportunity_name[:60] if opportunity.opportunity_name else "New Opportunity"
    return f"New NATO Opportunity: {opportunity.opportunity_code} - {name}"


def get_updated_opportunity_email_subject(opportunity: Opportunity, changed_fields: List[str]) -> str:
    """Get email subject for updated opportunity notification."""
    if changed_fields:
        fields_str = ", ".join(changed_fields[:3])
        if len(changed_fields) > 3:
            fields_str += f" and {len(changed_fields) - 3} more"
        return f"Updated NATO Opportunity: {opportunity.opportunity_code} ({fields_str})"
    return f"Updated NATO Opportunity: {opportunity.opportunity_code}"


def _get_opportunity_summary(opportunity: Opportunity) -> str:
    """
    Get opportunity summary, using Groq to generate one if summary is missing.
    
    Args:
        opportunity: Opportunity object
        
    Returns:
        Summary text for the opportunity
    """
    # Use existing summary if available
    if opportunity.summary:
        return opportunity.summary[:300]  # Limit length
    
    # Try to generate summary with Groq if available
    try:
        groq_client = get_groq_client()
        if groq_client.is_configured():
            client = groq_client.get_client()
            if client:
                prompt = f"""Generate a brief 2-3 sentence summary of this NATO opportunity:

Name: {opportunity.opportunity_name or 'N/A'}
Type: {opportunity.opportunity_type or 'N/A'}
NATO Body: {opportunity.nato_body or 'N/A'}
Contract Type: {opportunity.contract_type or 'N/A'}
Bid Closing Date: {opportunity.bid_closing_date or 'N/A'}

Provide a concise summary suitable for an email notification."""
                
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates concise summaries of NATO contracting opportunities."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                summary = response.choices[0].message.content.strip()
                logger.info(f"Generated summary for {opportunity.opportunity_code} using Groq")
                return summary[:300]
    except Exception as e:
        logger.warning(f"Could not generate summary with Groq: {e}")
    
    # Fallback to basic info
    return f"{opportunity.opportunity_name or 'NATO Opportunity'} ({opportunity.opportunity_code})"


def get_new_opportunity_email_html(opportunity: Opportunity, base_url: str = "") -> str:
    """
    Generate HTML email for new opportunity notification.
    
    Args:
        opportunity: Opportunity object
        base_url: Base URL of the website (for links)
        
    Returns:
        HTML email content
    """
    opportunity_url = f"{base_url}/#opportunities-section" if base_url else "#"
    summary = _get_opportunity_summary(opportunity)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #0ea5e9 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .opportunity-card {{ background: #f9fafb; border-left: 4px solid #0ea5e9; padding: 20px; margin: 20px 0; border-radius: 4px; }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-right: 8px; }}
            .badge-type {{ background: #dbeafe; color: #1e40af; }}
            .badge-body {{ background: #e5e7eb; color: #374151; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #0ea5e9; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
            .field {{ margin: 10px 0; }}
            .field-label {{ font-weight: 600; color: #4b5563; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>New NATO Opportunity Available</h1>
            </div>
            <div class="content">
                <p>A new NATO contracting opportunity has been posted:</p>
                
                <div class="opportunity-card">
                    <h2 style="margin-top: 0;">{opportunity.opportunity_name or 'NATO Opportunity'}</h2>
                    
                    <div style="margin: 15px 0;">
                        {f'<span class="badge badge-type">{opportunity.opportunity_type}</span>' if opportunity.opportunity_type else ''}
                        {f'<span class="badge badge-body">{opportunity.nato_body}</span>' if opportunity.nato_body else ''}
                        <span style="font-family: monospace; font-size: 12px; color: #6b7280;">{opportunity.opportunity_code}</span>
                    </div>
                    
                    <div class="field">
                        <span class="field-label">Bid Closing Date:</span> {format_opportunity_date(opportunity.bid_closing_date)}
                    </div>
                    {f'<div class="field"><span class="field-label">Clarification Deadline:</span> {format_opportunity_date(opportunity.clarification_deadline)}</div>' if opportunity.clarification_deadline else ''}
                    {f'<div class="field"><span class="field-label">Contract Type:</span> {opportunity.contract_type}</div>' if opportunity.contract_type else ''}
                    
                    <p style="margin-top: 15px;">{summary}</p>
                </div>
                
                <a href="{opportunity_url}" class="button">View All Opportunities</a>
                
                {f'<p><a href="{opportunity.url}" style="color: #0ea5e9;">View opportunity on NATO website</a></p>' if opportunity.url else ''}
                {f'<p><a href="{opportunity.pdf_url}" style="color: #0ea5e9;">Download PDF</a></p>' if opportunity.pdf_url else ''}
            </div>
            <div class="footer">
                <p>You're receiving this because you subscribed to NATO opportunity alerts.</p>
                <p><a href="{base_url}/unsubscribe" style="color: #6b7280;">Unsubscribe</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def get_updated_opportunity_email_html(opportunity: Opportunity, changed_fields: List[str], base_url: str = "") -> str:
    """
    Generate HTML email for updated opportunity notification.
    
    Args:
        opportunity: Opportunity object
        changed_fields: List of field names that changed
        base_url: Base URL of the website (for links)
        
    Returns:
        HTML email content
    """
    opportunity_url = f"{base_url}/#opportunities-section" if base_url else "#"
    
    changed_fields_list = ""
    if changed_fields:
        changed_fields_list = "<ul>"
        for field in changed_fields[:10]:  # Limit to 10 fields
            # Format field name for display
            field_display = field.replace("_", " ").title()
            changed_fields_list += f"<li>{field_display}</li>"
        if len(changed_fields) > 10:
            changed_fields_list += f"<li>... and {len(changed_fields) - 10} more</li>"
        changed_fields_list += "</ul>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .opportunity-card {{ background: #fffbeb; border-left: 4px solid #f59e0b; padding: 20px; margin: 20px 0; border-radius: 4px; }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-right: 8px; }}
            .badge-type {{ background: #dbeafe; color: #1e40af; }}
            .badge-body {{ background: #e5e7eb; color: #374151; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #f59e0b; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
            .field {{ margin: 10px 0; }}
            .field-label {{ font-weight: 600; color: #4b5563; }}
            .changes {{ background: #fef3c7; padding: 15px; border-radius: 4px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>NATO Opportunity Updated</h1>
            </div>
            <div class="content">
                <p>An opportunity you're following has been updated:</p>
                
                <div class="opportunity-card">
                    <h2 style="margin-top: 0;">{opportunity.opportunity_name or 'NATO Opportunity'}</h2>
                    
                    <div style="margin: 15px 0;">
                        {f'<span class="badge badge-type">{opportunity.opportunity_type}</span>' if opportunity.opportunity_type else ''}
                        {f'<span class="badge badge-body">{opportunity.nato_body}</span>' if opportunity.nato_body else ''}
                        <span style="font-family: monospace; font-size: 12px; color: #6b7280;">{opportunity.opportunity_code}</span>
                    </div>
                    
                    {f'<div class="changes"><strong>What Changed:</strong>{changed_fields_list}</div>' if changed_fields_list else ''}
                    
                    <div class="field">
                        <span class="field-label">Bid Closing Date:</span> {format_opportunity_date(opportunity.bid_closing_date)}
                    </div>
                    {f'<div class="field"><span class="field-label">Clarification Deadline:</span> {format_opportunity_date(opportunity.clarification_deadline)}</div>' if opportunity.clarification_deadline else ''}
                </div>
                
                <a href="{opportunity_url}" class="button">View All Opportunities</a>
                
                {f'<p><a href="{opportunity.url}" style="color: #f59e0b;">View opportunity on NATO website</a></p>' if opportunity.url else ''}
                {f'<p><a href="{opportunity.pdf_url}" style="color: #f59e0b;">Download Updated PDF</a></p>' if opportunity.pdf_url else ''}
            </div>
            <div class="footer">
                <p>You're receiving this because you subscribed to NATO opportunity alerts.</p>
                <p><a href="{base_url}/unsubscribe" style="color: #6b7280;">Unsubscribe</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def get_new_opportunity_email_text(opportunity: Opportunity) -> str:
    """Generate plain text email for new opportunity notification."""
    summary = _get_opportunity_summary(opportunity)
    
    text = f"""
New NATO Opportunity Available

A new NATO contracting opportunity has been posted:

{opportunity.opportunity_name or 'NATO Opportunity'}
Code: {opportunity.opportunity_code}
Type: {opportunity.opportunity_type or 'N/A'}
NATO Body: {opportunity.nato_body or 'N/A'}

Bid Closing Date: {format_opportunity_date(opportunity.bid_closing_date)}
"""
    if opportunity.clarification_deadline:
        text += f"Clarification Deadline: {format_opportunity_date(opportunity.clarification_deadline)}\n"
    if opportunity.contract_type:
        text += f"Contract Type: {opportunity.contract_type}\n"
    
    text += f"\nSummary: {summary}\n"
    text += f"\nView opportunity: {opportunity.url or 'N/A'}\n"
    if opportunity.pdf_url:
        text += f"Download PDF: {opportunity.pdf_url}\n"
    
    return text


def get_updated_opportunity_email_text(opportunity: Opportunity, changed_fields: List[str]) -> str:
    """Generate plain text email for updated opportunity notification."""
    text = f"""
NATO Opportunity Updated

An opportunity you're following has been updated:

{opportunity.opportunity_name or 'NATO Opportunity'}
Code: {opportunity.opportunity_code}
"""
    if changed_fields:
        text += f"\nWhat Changed:\n"
        for field in changed_fields[:10]:
            field_display = field.replace("_", " ").title()
            text += f"  - {field_display}\n"
        if len(changed_fields) > 10:
            text += f"  - ... and {len(changed_fields) - 10} more\n"
    
    text += f"\nBid Closing Date: {format_opportunity_date(opportunity.bid_closing_date)}\n"
    text += f"\nView opportunity: {opportunity.url or 'N/A'}\n"
    if opportunity.pdf_url:
        text += f"Download Updated PDF: {opportunity.pdf_url}\n"
    
    return text


def get_daily_summary_email_subject(new_count: int, amended_count: int) -> str:
    """Get email subject for daily summary."""
    parts = []
    if new_count > 0:
        parts.append(f"{new_count} new")
    if amended_count > 0:
        parts.append(f"{amended_count} updated")
    
    if not parts:
        return "NATO Opportunities Update"
    
    return f"NATO Opportunities: {', '.join(parts)}"


def get_daily_summary_email_html(
    new_opportunities: List[Opportunity],
    amended_opportunities: List[Opportunity],
    base_url: str = ""
) -> str:
    """
    Generate HTML email for daily summary of all changes.
    
    Args:
        new_opportunities: List of newly created opportunities
        amended_opportunities: List of amended opportunities
        base_url: Base URL of the website (for links)
        
    Returns:
        HTML email content
    """
    opportunity_url = f"{base_url}/#opportunities-section" if base_url else "#"
    
    new_section = ""
    if new_opportunities:
        new_section = "<div style='margin: 20px 0;'>"
        new_section += "<h2 style='color: #0ea5e9; margin-bottom: 15px;'>🆕 New Opportunities</h2>"
        for opp in new_opportunities:
            summary = _get_opportunity_summary(opp)
            new_section += f"""
            <div style='background: #f9fafb; border-left: 4px solid #0ea5e9; padding: 15px; margin: 15px 0; border-radius: 4px;'>
                <h3 style='margin-top: 0; margin-bottom: 10px;'>{opp.opportunity_name or 'NATO Opportunity'}</h3>
                <div style='margin: 10px 0;'>
                    {f'<span style="display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-right: 8px; background: #dbeafe; color: #1e40af;">{opp.opportunity_type}</span>' if opp.opportunity_type else ''}
                    {f'<span style="display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-right: 8px; background: #e5e7eb; color: #374151;">{opp.nato_body}</span>' if opp.nato_body else ''}
                    <span style="font-family: monospace; font-size: 12px; color: #6b7280;">{opp.opportunity_code}</span>
                </div>
                <div style='margin: 10px 0;'>
                    <strong>Bid Closing Date:</strong> {format_opportunity_date(opp.bid_closing_date)}
                </div>
                <p style='margin: 10px 0;'>{summary[:200]}{'...' if len(summary) > 200 else ''}</p>
                {f'<p><a href="{opp.url}" style="color: #0ea5e9;">View on NATO website</a></p>' if opp.url else ''}
            </div>
            """
        new_section += "</div>"
    
    amended_section = ""
    if amended_opportunities:
        amended_section = "<div style='margin: 20px 0;'>"
        amended_section += "<h2 style='color: #f59e0b; margin-bottom: 15px;'>📝 Updated Opportunities</h2>"
        for opp in amended_opportunities:
            changed_fields = opp.last_changed_fields or []
            changed_fields_list = ""
            if changed_fields:
                changed_fields_list = "<ul style='margin: 10px 0; padding-left: 20px;'>"
                for field in changed_fields[:10]:
                    field_display = field.replace("_", " ").title()
                    changed_fields_list += f"<li>{field_display}</li>"
                if len(changed_fields) > 10:
                    changed_fields_list += f"<li>... and {len(changed_fields) - 10} more</li>"
                changed_fields_list += "</ul>"
            
            amended_section += f"""
            <div style='background: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; margin: 15px 0; border-radius: 4px;'>
                <h3 style='margin-top: 0; margin-bottom: 10px;'>{opp.opportunity_name or 'NATO Opportunity'}</h3>
                <div style='margin: 10px 0;'>
                    {f'<span style="display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-right: 8px; background: #dbeafe; color: #1e40af;">{opp.opportunity_type}</span>' if opp.opportunity_type else ''}
                    {f'<span style="display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-right: 8px; background: #e5e7eb; color: #374151;">{opp.nato_body}</span>' if opp.nato_body else ''}
                    <span style="font-family: monospace; font-size: 12px; color: #6b7280;">{opp.opportunity_code}</span>
                </div>
                {f'<div style="background: #fef3c7; padding: 10px; border-radius: 4px; margin: 10px 0;"><strong>What Changed:</strong>{changed_fields_list}</div>' if changed_fields_list else ''}
                <div style='margin: 10px 0;'>
                    <strong>Bid Closing Date:</strong> {format_opportunity_date(opp.bid_closing_date)}
                </div>
                {f'<p><a href="{opp.url}" style="color: #f59e0b;">View on NATO website</a></p>' if opp.url else ''}
            </div>
            """
        amended_section += "</div>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #0ea5e9 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #0ea5e9; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>NATO Opportunities Update</h1>
                <p style="margin: 10px 0 0 0;">
                    {len(new_opportunities)} new opportunity{'ies' if len(new_opportunities) != 1 else ''}
                    {', ' if new_opportunities and amended_opportunities else ''}
                    {len(amended_opportunities)} updated opportunity{'ies' if len(amended_opportunities) != 1 else '' if amended_opportunities else ''}
                </p>
            </div>
            <div class="content">
                {new_section}
                {amended_section}
                
                <a href="{opportunity_url}" class="button">View All Opportunities</a>
            </div>
            <div class="footer">
                <p>You're receiving this because you subscribed to NATO opportunity alerts.</p>
                <p><a href="{base_url}/unsubscribe" style="color: #6b7280;">Unsubscribe</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def get_daily_summary_email_text(
    new_opportunities: List[Opportunity],
    amended_opportunities: List[Opportunity]
) -> str:
    """Generate plain text email for daily summary."""
    text = f"""
NATO Opportunities Update

Summary of changes:
- {len(new_opportunities)} new opportunity{'ies' if len(new_opportunities) != 1 else ''}
- {len(amended_opportunities)} updated opportunity{'ies' if len(amended_opportunities) != 1 else ''}

"""
    
    if new_opportunities:
        text += "\n🆕 NEW OPPORTUNITIES:\n"
        text += "=" * 50 + "\n"
        for opp in new_opportunities:
            summary = _get_opportunity_summary(opp)
            text += f"\n{opp.opportunity_name or 'NATO Opportunity'}\n"
            text += f"Code: {opp.opportunity_code}\n"
            text += f"Type: {opp.opportunity_type or 'N/A'}\n"
            text += f"NATO Body: {opp.nato_body or 'N/A'}\n"
            text += f"Bid Closing Date: {format_opportunity_date(opp.bid_closing_date)}\n"
            text += f"Summary: {summary[:150]}...\n"
            if opp.url:
                text += f"View: {opp.url}\n"
            text += "\n" + "-" * 50 + "\n"
    
    if amended_opportunities:
        text += "\n📝 UPDATED OPPORTUNITIES:\n"
        text += "=" * 50 + "\n"
        for opp in amended_opportunities:
            changed_fields = opp.last_changed_fields or []
            text += f"\n{opp.opportunity_name or 'NATO Opportunity'}\n"
            text += f"Code: {opp.opportunity_code}\n"
            if changed_fields:
                text += f"What Changed: {', '.join(changed_fields[:5])}\n"
            text += f"Bid Closing Date: {format_opportunity_date(opp.bid_closing_date)}\n"
            if opp.url:
                text += f"View: {opp.url}\n"
            text += "\n" + "-" * 50 + "\n"
    
    return text

