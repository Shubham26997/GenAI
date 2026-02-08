import re

def parse_markdown_to_html(text):
    """Convert markdown-style formatting to HTML."""
    # Convert # headings to h3 tags (for main title/header)
    text = re.sub(r'^# (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    
    # Convert ## or ### headings to h2 tags
    text = re.sub(r'^#{2,3} (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    
    # Convert **bold** to <strong> tags
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Remove horizontal separators (---)
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    
    # Convert KEY TAKEAWAYS section to proper list format
    # Match "KEY TAKEAWAYS" (possibly inside <h2>) followed by bullet points
    text = re.sub(
        r'(?:<h2>)?\s*KEY TAKEAWAYS\s*(?:</h2>)?\s*([\s\S]*?)(?=<h[23]>|$)',
        lambda m: '<h2>Key Takeaways</h2><ul>' + 
                  re.sub(r'^[*-]\s+(.+)$', r'<li>\1</li>', m.group(1).strip(), flags=re.MULTILINE) + 
                  '</ul>',
        text,
        flags=re.IGNORECASE
    )
    
    # Convert line breaks to <br> but avoid triple breaks
    text = text.replace('\n\n', '<br>')
    
    return text

def save_as_html(content, filename="news_report.html", return_content=False):
    """Saves the news content as a styled HTML file for mailing."""
    # Parse markdown formatting
    formatted_content = parse_markdown_to_html(content)
    
    html_template = f"""<!DOCTYPE html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light dark">
    <meta name="supported-color-schemes" content="light dark">
    <title>AI & Tech News Brief</title>
    <style>
        :root {{
            color-scheme: light dark;
            supported-color-schemes: light dark;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-text-size-adjust: none;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #667eea;
            background-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 40px 20px;
            color: #1a1a1a;
            line-height: 1.7;
        }}
        
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }}
        
        .header {{
            text-align: center;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 30px;
            padding-bottom: 20px;
        }}
        
        h1 {{
            color: #4a5568;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .subtitle {{
            color: #718096;
            font-size: 14px;
        }}
        
        .content {{
            font-size: 16px;
            color: #2d3748;
        }}
        
        h2 {{
            font-size: 20px;
            color: #2d3748;
            margin-top: 30px;
            margin-bottom: 12px;
            padding-left: 15px;
            border-left: 4px solid #667eea;
        }}
        
        h3 {{
            font-size: 18px;
            color: #059669;
            background-color: #ecfdf5;
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
            text-transform: uppercase;
        }}
        
        ul {{
            margin: 15px 0;
            padding-left: 20px;
        }}
        
        li {{
            margin-bottom: 10px;
        }}
        
        strong {{
            color: #1a202c;
            background-color: #fff9db;
            padding: 0 4px;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #718096;
            font-size: 12px;
        }}

        /* DARK MODE - STANDARD */
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #000000 !important;
                background-image: none !important;
            }}
            .container {{
                background-color: #1a1a1a !important;
                color: #ffffff !important;
                border: 1px solid #333333 !important;
            }}
            h1, h2, .content, li, strong {{
                color: #ffffff !important;
            }}
            .subtitle, .footer {{
                color: #a0aec0 !important;
            }}
            .content {{
                background-color: #1a1a1a !important;
            }}
            h3 {{
                background-color: #064e3b !important;
                color: #34d399 !important;
            }}
            strong {{
                background-color: #2d3748 !important;
            }}
        }}

        /* GMAIL DARK MODE HACKS */
        [data-ogsc] body, [data-ogsb] body {{ background-color: #000000 !important; }}
        [data-ogsc] .container, [data-ogsb] .container {{ background-color: #1a1a1a !important; }}
        [data-ogsc] h1, [data-ogsb] h1, [data-ogsc] h2, [data-ogsb] h2, [data-ogsc] .content, [data-ogsb] .content, [data-ogsc] li, [data-ogsb] li {{ color: #ffffff !important; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI & Tech News Brief</h1>
            <p class="subtitle">Your curated digest of the latest developments</p>
        </div>
        <div class="content">
            {formatted_content}
        </div>
        <div class="footer">
            <p>Powered by AI News Engine</p>
            <p>&copy; Shubham Newsletter</p>
        </div>
    </div>
</body>
</html>"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"Successfully saved news to {filename}")
    if return_content:
        return html_template